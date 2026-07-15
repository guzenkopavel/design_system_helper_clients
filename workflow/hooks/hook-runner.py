#!/usr/bin/env python3
"""Portable hook policy runner. Runtime adapters only forward JSON to this SSOT."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


ALLOW = "allow"
WARN = "warn"
DENY = "deny"
COMPOUND = {";", "&&", "||", "|", "&"}
MAX_SHELL_DEPTH = 3


def repository_root(start: Path | None = None) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=start or Path.cwd(),
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError("not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def load_gate(repo: Path):
    path = repo / "workflow/scripts/pre-commit-check.py"
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("portable_pre_commit_gate", path)
    if spec is None or spec.loader is None:
        raise ValueError("pre-commit gate is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
    return value if isinstance(value, dict) else {"value": value}


def nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def command_from(payload: dict[str, Any]) -> str:
    for value in (
        payload.get("command"), nested(payload, "tool_input", "command"),
        nested(payload, "input", "command"), nested(payload, "args", "command"),
    ):
        if isinstance(value, str):
            return value
    return ""


def paths_from(payload: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for container in (payload, payload.get("tool_input"), payload.get("input"), payload.get("args")):
        if not isinstance(container, dict):
            continue
        for key in (
            "file_path", "filePath", "path", "target_file", "targetFile",
            "notebook_path", "notebookPath", "paths", "files",
        ):
            if key in container:
                values.append(container[key])
    result: list[str] = []
    for value in values:
        candidates = value if isinstance(value, list) else [value]
        for item in candidates:
            if isinstance(item, str) and item not in result:
                result.append(item)
    return result


def relative_path(repo: Path, raw: str) -> str | None:
    value = Path(raw)
    try:
        if value.is_absolute():
            return value.resolve().relative_to(repo).as_posix()
    except ValueError:
        return None
    normalized = PurePosixPath(raw).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return None if ".." in PurePosixPath(normalized).parts else normalized


def shell_segments(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in COMPOUND or token in {";;", "&&", "||"}:
            if segments[-1]:
                segments.append([])
        else:
            segments[-1].append(token)
    return [item for item in segments if item]


def command_index(segment: list[str]) -> int:
    index = 0
    while index < len(segment) and ("=" in segment[index] and not segment[index].startswith("-")):
        index += 1
    while index < len(segment):
        executable = Path(segment[index]).name
        if executable == "command":
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                index += 1
            continue
        if executable == "env":
            index += 1
            while index < len(segment):
                token = segment[index]
                if token.startswith("-") or ("=" in token and not token.startswith("-")):
                    index += 1
                    continue
                break
            continue
        if executable == "rtk":
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                index += 1
            continue
        break
    return index


def nested_shell_command(segment: list[str]) -> str | None:
    index = command_index(segment)
    if index >= len(segment) or Path(segment[index]).name not in {"sh", "bash"}:
        return None
    args = segment[index + 1:]
    for position, token in enumerate(args):
        if token.startswith("--"):
            continue
        if re.fullmatch(r"-[A-Za-z]+", token) and "c" in token[1:] and position + 1 < len(args):
            return args[position + 1]
    return None


def git_invocation(segment: list[str]) -> tuple[str, list[str]] | None:
    index = command_index(segment)
    if index >= len(segment) or Path(segment[index]).name != "git":
        return None
    index += 1
    while index < len(segment):
        token = segment[index]
        if token in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
            index += 2
            continue
        if token.startswith(("--git-dir=", "--work-tree=", "--namespace=", "--config-env=")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token, segment[index + 1:]
    return None


def has_flag(args: list[str], short: str, long: str) -> bool:
    return long in args or any(item.startswith("-") and not item.startswith("--") and short in item[1:] for item in args)


def command_policy(repo: Path, payload: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    explicit = bool(payload.get("explicit_authorization"))

    def inspect(command: str, depth: int) -> None:
        for segment in shell_segments(command):
            nested_command = nested_shell_command(segment)
            if nested_command is not None:
                if depth >= MAX_SHELL_DEPTH:
                    reasons.append("nested shell command exceeds inspection depth")
                else:
                    inspect(nested_command, depth + 1)
                continue
            invocation = git_invocation(segment)
            if invocation is None:
                continue
            subcommand, args = invocation
            if subcommand == "commit" and "--no-verify" in args:
                reasons.append("git commit --no-verify bypasses the mandatory gate")
                continue
            if subcommand == "reset" and "--hard" in args:
                reasons.append("git reset --hard can discard owner work")
            elif subcommand == "clean" and has_flag(args, "f", "--force"):
                reasons.append("git clean --force can delete owner files")
            elif subcommand == "branch" and "-D" in args:
                reasons.append("git branch -D is destructive")
            elif subcommand in {"checkout", "restore"} and any(item in {".", ":/"} for item in args):
                reasons.append(f"git {subcommand} may discard the whole worktree")
            elif subcommand == "push" and has_flag(args, "f", "--force") and "--force-with-lease" not in args:
                reasons.append("force push without --force-with-lease is forbidden")
            elif subcommand in {"rebase", "filter-branch", "filter-repo"} and not explicit:
                reasons.append(f"git {subcommand} requires explicit authorization")
            elif subcommand == "commit" and "--amend" in args and not explicit:
                reasons.append("git commit --amend requires explicit authorization")
            if subcommand == "commit" and not reasons:
                gate = load_gate(repo).evaluate(repo)
                if gate.get("status") != "PASS":
                    reasons.append(f"pre-commit gate is {gate.get('status', 'UNKNOWN')}")

    inspect(command_from(payload), 0)
    return (DENY, reasons) if reasons else (ALLOW, [])


def edit_policy(repo: Path, payload: dict[str, Any]) -> tuple[str, list[str]]:
    gate = load_gate(repo)
    adapters, adapter_errors = gate.load_adapter_state(repo)
    reasons: list[str] = []
    production: list[str] = []
    for raw in paths_from(payload):
        path = relative_path(repo, raw)
        if path is None:
            reasons.append("edit path escapes repository")
            continue
        invalid_root = next((root for root in adapter_errors if gate.path_under(path, [root])), None)
        if invalid_root:
            reasons.append(f"{invalid_root} adapter is missing or invalid")
            continue
        profile = None
        adapter = gate.adapter_for_production(path, adapters)
        owner = next((
            item for item in adapters
            if gate.path_under(path, [str(value) for value in item["protected_roots"] + item["production_exclusions"]])
        ), None)
        if adapter:
            profile = adapter["pre_commit"]
            production.append(path)
        elif owner:
            profile = owner["pre_commit"]
        secret_patterns = list(gate.COMMON_SECRET_PATHS) + (list(profile["secret_globs"]) if profile else [])
        if gate.glob_match(path, secret_patterns):
            reasons.append(f"secret/key path is not editable: {path}")
            continue
    if production:
        coverage = gate.coverage_report(repo, production)
        if coverage.get("status") != "PASS":
            reasons.append("platform production edit is not covered by an active task")
    return (DENY, reasons) if reasons else (ALLOW, [])


def post_edit_policy(repo: Path, payload: dict[str, Any]) -> tuple[str, list[str]]:
    gate = load_gate(repo)
    reasons: list[str] = []
    content = payload.get("content") or nested(payload, "tool_input", "content")
    for raw in paths_from(payload):
        path = relative_path(repo, raw)
        if path is None:
            continue
        if gate.active_spec(path):
            value = content
            if not isinstance(value, str):
                target = repo / path
                value = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
            if gate.PLACEHOLDER_RE.search(value.encode()):
                reasons.append(f"active specification still contains a placeholder: {path}")
        if path.startswith(("iOS/", "Android/")) and re.search(
            r"(?:Security|Entitlements|Info\.plist|AndroidManifest|network_security|build\.gradle)", path, re.I,
        ):
            reasons.append(f"review platform security evidence after editing: {path}")
    return (WARN, reasons) if reasons else (ALLOW, [])


def evaluate(repo: Path, event: str, payload: dict[str, Any]) -> dict[str, Any]:
    if event == "pre-tool":
        command = command_from(payload)
        decision, reasons = command_policy(repo, payload) if command else edit_policy(repo, payload)
    elif event == "post-edit":
        decision, reasons = post_edit_policy(repo, payload)
    else:
        decision, reasons = DENY, [f"unsupported hook event: {event}"]
    return {"decision": decision, "event": event, "reasons": reasons}


def runtime_report(report: dict[str, Any], runtime: str) -> dict[str, Any]:
    message = "; ".join(report["reasons"])
    if runtime == "cursor":
        if report["event"] == "post-edit":
            return {"additional_context": message} if message else {}
        return {
            "permission": "deny" if report["decision"] == DENY else "allow",
            "user_message": message,
        }
    if runtime == "claude":
        if report["event"] == "post-edit":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                }
            } if message else {}
        if report["decision"] == DENY:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        return {}
    return {**report, "runtime": runtime}


def configure_git(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "hooks@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Hook Test"], cwd=repo, check=True)


def write_fixture(repo: Path) -> None:
    (repo / "workflow/scripts").mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / "scripts"
    for name in ("pre-commit-check.py", "platform_rule_profiles.py"):
        (repo / "workflow/scripts" / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")
    for platform, suffix in (("iOS", ".swift"), ("Android", ".kt")):
        contract = {
            "platform_name": platform, "platform_root": platform, "package_root": f"{platform}/specs",
            "active_changes_namespace": "changes", "production_roots": [platform],
            "protected_roots": [f"{platform}/specs", f"{platform}/workflow"],
            "production_exclusions": [f"{platform}/specs", f"{platform}/workflow"],
            "pre_commit": {"source_suffixes": [suffix], "generated_globs": [f"{platform}/**/build/**"],
                "secret_globs": [f"{platform}/**/*.key"],
                "security_sensitive_globs": [f"{platform}/**/*Security*"],
                "ui_globs": [f"{platform}/**/*View{suffix}"], "localization_globs": [f"{platform}/**/Localizable.*"],
                "project_globs": [f"{platform}/**/Project.config"], "tool_globs": {"build": [f"{platform}/**/Project.config"]}},
        }
        path = repo / f"{platform}/workflow/platform-contract.json"
        path.parent.mkdir(parents=True); path.write_text(json.dumps(contract), encoding="utf-8")


def write_active_task(repo: Path, platform: str, candidate: str, scopes: list[str]) -> None:
    package = repo / f"{platform}/specs/sample/changes/native-hooks"
    package.mkdir(parents=True, exist_ok=True)
    (package / "meta.json").write_text(json.dumps({"status": "implementing"}), encoding="utf-8")
    (package / "plan").mkdir()
    (package / "plan/task-001.md").write_text(
        "# Native hook task\n"
        f"- Engineering scopes: {json.dumps(scopes)}\n"
        "- Status: pending\n"
        "- Evidence: none\n"
        f"- Paths: proposed: {candidate}\n",
        encoding="utf-8",
    )


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); configure_git(repo); write_fixture(repo)
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
        assert command_policy(repo, {"command": "echo 'git reset --hard'"})[0] == ALLOW
        for command in (
            "git reset --hard", "cd app && git clean -fd", "git -C app branch -D old",
            "git restore .", "git push --force origin main", "git commit --no-verify -m x",
            "rtk git reset --hard", "/usr/bin/git clean -fd",
            "command git restore .", "env SAFE=1 git branch -D old",
            "/usr/bin/env -i git -C app reset --hard",
            "sh -c 'git reset --hard'", "sh -lc 'rtk git clean -fd'",
            "/bin/bash -c 'command git restore .'",
            "env SAFE=1 /bin/sh -lc 'git branch -D old'",
            "bash -lc \"sh -c 'git reset --hard'\"",
            "/bin/bash --norc -c 'git reset --hard'",
            "/bin/bash --rcfile /dev/null -lc 'git clean -fd'",
            "/bin/bash -O extglob -c 'git reset --hard'",
            "/bin/bash -o posix -c 'git clean -fd'",
            "/bin/bash +O extglob -c 'git reset --hard'",
            "/bin/bash +o posix -c 'git clean -fd'",
        ):
            assert command_policy(repo, {"command": command})[0] == DENY, command
        assert command_policy(repo, {"command": "echo \"sh -c 'git reset --hard'\""})[0] == ALLOW
        assert command_policy(repo, {"command": "git push --force-with-lease origin main", "explicit_authorization": True})[0] == ALLOW
        assert command_policy(repo, {"command": "git rebase main"})[0] == DENY
        assert command_policy(repo, {"command": "git rebase main", "explicit_authorization": True})[0] == ALLOW
        assert command_policy(repo, {"tool_input": {"command": "rtk git reset --hard"}})[0] == DENY
        assert command_policy(repo, {"args": {"command": "/usr/bin/git clean -fd"}})[0] == DENY
        assert edit_policy(repo, {"tool_input": {"file_path": "workflow/rules/example.md"}})[0] == ALLOW
        assert edit_policy(repo, {"tool_name": "Write", "tool_input": {"file_path": "specs/product/sample/spec.md"}})[0] == ALLOW
        assert edit_policy(repo, {"args": {"filePath": ".agents/skills/example/SKILL.md"}})[0] == ALLOW
        write_active_task(repo, "iOS", "iOS/App.xcodeproj/project.pbxproj", ["xcode"])
        write_active_task(repo, "Android", "Android/App/Security.kt", ["application"])
        assert edit_policy(repo, {"tool_input": {"file_path": "iOS/specs/sample/changes/native-hooks/plan/task-001.md"}})[0] == ALLOW
        assert edit_policy(repo, {"tool_input": {"file_path": "iOS/App.xcodeproj/project.pbxproj"}})[0] == ALLOW
        assert edit_policy(repo, {"tool_name": "Write", "tool_input": {"file_path": "Android/App/Security.kt"}})[0] == ALLOW
        assert edit_policy(repo, {"tool": "write", "args": {"filePath": "Android/App/Security.kt"}})[0] == ALLOW
        assert edit_policy(repo, {"file_path": "Android/local.properties"})[0] == DENY
        assert edit_policy(repo, {"file_path": ".env"})[0] == DENY
        assert edit_policy(repo, {"tool": "write", "args": {"filePath": "iOS/Uncovered.swift"}})[0] == DENY
        ios_contract = repo / "iOS/workflow/platform-contract.json"
        contract_body = ios_contract.read_text(encoding="utf-8")
        ios_contract.write_text("{ malformed\n", encoding="utf-8")
        assert edit_policy(repo, {"tool_input": {"file_path": "iOS/App.xcodeproj/project.pbxproj"}})[0] == DENY
        ios_contract.write_text(contract_body, encoding="utf-8")
        assert post_edit_policy(repo, {"file_path": "workflow/templates/example.md", "content": "TODO"})[0] == ALLOW
        assert post_edit_policy(repo, {"file_path": "specs/product/sample/spec.md", "content": "TODO"})[0] == WARN
        cursor_deny = runtime_report(evaluate(repo, "pre-tool", {"tool_input": {"command": "rtk git reset --hard"}}), "cursor")
        assert cursor_deny["permission"] == "deny" and "user_message" in cursor_deny
        cursor_allow = runtime_report(evaluate(repo, "pre-tool", {"tool_input": {"file_path": "workflow/README.md"}}), "cursor")
        assert cursor_allow["permission"] == "allow"
        warning_report = {"decision": WARN, "event": "post-edit", "reasons": ["review warning"]}
        cursor_warning = runtime_report(warning_report, "cursor")
        assert cursor_warning == {"additional_context": "review warning"}
        claude_warning = runtime_report(warning_report, "claude")
        assert claude_warning == {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "review warning"}}
        claude_deny = runtime_report({"decision": DENY, "event": "pre-tool", "reasons": ["blocked"]}, "claude")
        assert claude_deny["hookSpecificOutput"]["permissionDecision"] == "deny"
        codex_warning = runtime_report(warning_report, "codex")
        assert codex_warning["decision"] == WARN and codex_warning["runtime"] == "codex"
    print("hook-runner self-test: PASS (git guards, platform edit guards, post-edit warnings)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", default="direct")
    parser.add_argument("--event", choices=("pre-tool", "post-edit"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.event:
        parser.error("--event is required")
    try:
        repo = repository_root(args.root)
        report = evaluate(repo, args.event, read_payload())
    except (OSError, ValueError) as error:
        report = {"decision": DENY, "event": args.event, "reasons": [str(error)]}
    rendered = runtime_report(report, args.runtime)
    print(json.dumps(rendered, ensure_ascii=False, sort_keys=True))
    if report["decision"] == DENY:
        print("; ".join(report["reasons"]), file=sys.stderr)
    return 2 if report["decision"] == DENY else 0


if __name__ == "__main__":
    raise SystemExit(main())
