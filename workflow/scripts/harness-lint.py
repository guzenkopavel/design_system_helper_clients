#!/usr/bin/env python3
"""Deterministic structural checks for the repository workflow harness."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import unquote

from platform_rule_profiles import (
    PHASES,
    RuleProfileError,
    validate_capabilities,
    validate_pre_commit_profile,
    validate_profiles,
)


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
DISPATCH_RE = re.compile(
    r"(?:HANDOFF|role|роли|роль)\s+[`']([a-z0-9-]+)[`']",
    re.IGNORECASE,
)
NAME_RE = re.compile(r"^(?:[a-z0-9._-]+|[A-Z0-9_]+)\.(?:md|py|toml)$")
RUNTIME_AGENT_DIRS = {
    "codex": (".codex/agents", ".toml"),
    "claude": (".claude/agents", ".md"),
    "cursor": (".cursor/agents", ".md"),
    "opencode": (".opencode/agents", ".md"),
}
EXCLUDED_DIRS = {
    ".git",
    ".build",
    ".gradle",
    ".idea",
    ".swiftpm",
    "DerivedData",
    "build",
    "node_modules",
    "__pycache__",
}


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip() or os.getcwd()).resolve()


def iter_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    result: list[Path] = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in EXCLUDED_DIRS]
        for filename in files:
            path = Path(base) / filename
            if path.suffix in suffixes:
                result.append(path)
    return sorted(result)


def finding(severity: str, check: str, path: Path | str, detail: str) -> dict[str, str]:
    return {
        "severity": severity,
        "check": check,
        "file": str(path).replace(os.sep, "/"),
        "detail": detail,
    }


def relative(path: Path, root: Path) -> Path:
    return path.resolve().relative_to(root)


def check_links(root: Path, markdown_files: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = unquote(match.group(1).strip())
            target = raw.split("#", 1)[0]
            if not target or raw.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if any(marker in target for marker in ("<", ">", "...")):
                continue
            candidates = ((path.parent / target).resolve(), (root / target).resolve())
            if not any(candidate.exists() for candidate in candidates):
                findings.append(
                    finding("critical", "broken-link", relative(path, root), raw)
                )
    return findings


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str | None]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return {}, "missing YAML frontmatter"
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, "unterminated YAML frontmatter"
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            return {}, f"invalid frontmatter line: {line}"
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, None


def check_skills(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    skills_root = root / ".agents" / "skills"
    if not skills_root.is_dir():
        return [finding("critical", "skills-root", ".agents/skills", "directory is missing")]

    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            findings.append(finding("critical", "skill-file", relative(skill_dir, root), "SKILL.md is missing"))
            continue
        metadata, error = parse_frontmatter(skill_file)
        if error:
            findings.append(finding("critical", "skill-frontmatter", relative(skill_file, root), error))
            continue
        extra = sorted(set(metadata) - {"name", "description"})
        if metadata.get("name") != skill_dir.name:
            findings.append(
                finding(
                    "critical",
                    "skill-name",
                    relative(skill_file, root),
                    f"name '{metadata.get('name')}' does not match directory '{skill_dir.name}'",
                )
            )
        if not metadata.get("description"):
            findings.append(finding("critical", "skill-description", relative(skill_file, root), "description is missing"))
        if extra:
            findings.append(finding("warning", "skill-frontmatter", relative(skill_file, root), f"unexpected keys: {', '.join(extra)}"))

        openai_metadata = skill_dir / "agents" / "openai.yaml"
        if not openai_metadata.is_file():
            findings.append(
                finding(
                    "warning",
                    "codex-skill-metadata",
                    relative(skill_dir, root),
                    "agents/openai.yaml is missing",
                )
            )

        canonical = root / "workflow" / "phases" / f"{skill_dir.name}.md"
        if not canonical.is_file():
            findings.append(
                finding("warning", "skill-canonical", relative(skill_file, root), f"missing {relative(canonical, root)}")
            )

        claude_command = root / ".claude" / "commands" / f"{skill_dir.name}.md"
        if not claude_command.is_file():
            findings.append(
                finding(
                    "critical",
                    "claude-skill-command",
                    relative(skill_file, root),
                    f"missing .claude/commands/{skill_dir.name}.md",
                )
            )
        else:
            claude_metadata, claude_error = parse_frontmatter(claude_command)
            if claude_error:
                findings.append(
                    finding(
                        "critical",
                        "claude-command-frontmatter",
                        relative(claude_command, root),
                        claude_error,
                    )
                )
            else:
                if not claude_metadata.get("description"):
                    findings.append(
                        finding(
                            "critical",
                            "claude-command-description",
                            relative(claude_command, root),
                            "description is missing",
                        )
                    )
            command_text = claude_command.read_text(encoding="utf-8")
            portable_pointer = f".agents/skills/{skill_dir.name}/SKILL.md"
            if portable_pointer not in command_text:
                findings.append(
                    finding(
                        "critical",
                        "claude-command-binding",
                        relative(claude_command, root),
                        f"portable pointer is missing: {portable_pointer}",
                    )
                )
            if "$ARGUMENTS" not in command_text:
                findings.append(
                    finding(
                        "warning",
                        "claude-command-arguments",
                        relative(claude_command, root),
                        "$ARGUMENTS forwarding is missing",
                    )
                )

        duplicate_claude_skill = (
            root / ".claude" / "skills" / skill_dir.name / "SKILL.md"
        )
        if duplicate_claude_skill.is_file():
            findings.append(
                finding(
                    "critical",
                    "claude-duplicate-skill",
                    relative(duplicate_claude_skill, root),
                    "use .claude/commands; duplicate skill shadows portable SSOT",
                )
            )
        opencode_command = root / ".opencode" / "commands" / f"{skill_dir.name}.md"
        if not opencode_command.is_file():
            findings.append(
                finding(
                    "critical",
                    "opencode-skill-command",
                    relative(skill_file, root),
                    f"missing .opencode/commands/{skill_dir.name}.md",
                )
            )
    return findings


def read_agents(root: Path) -> tuple[set[str], list[dict[str, str]]]:
    names: set[str] = set()
    findings: list[dict[str, str]] = []
    canonical_root = root / "workflow" / "roles"
    if not canonical_root.is_dir():
        return names, [
            finding("critical", "roles-root", "workflow/roles", "directory is missing")
        ]
    canonical_dirs = [canonical_root]
    ios_roles = root / "iOS" / "workflow" / "roles"
    if ios_roles.is_dir():
        canonical_dirs.append(ios_roles)
    android_roles = root / "Android" / "workflow" / "roles"
    if android_roles.is_dir():
        canonical_dirs.append(android_roles)
    canonical_names = {
        path.stem for directory in canonical_dirs for path in directory.glob("*.md")
    }

    for runtime, (directory, suffix) in RUNTIME_AGENT_DIRS.items():
        agents_root = root / directory
        if not agents_root.is_dir():
            findings.append(
                finding("critical", "agents-root", directory, f"{runtime} agents directory is missing")
            )
            continue

        runtime_names: set[str] = set()
        for path in sorted(agents_root.glob(f"*{suffix}")):
            if suffix == ".toml":
                try:
                    data = tomllib.loads(path.read_text(encoding="utf-8"))
                except tomllib.TOMLDecodeError as error:
                    findings.append(finding("critical", "agent-toml", relative(path, root), str(error)))
                    continue
                name = data.get("name")
            else:
                metadata, error = parse_frontmatter(path)
                if error:
                    findings.append(finding("critical", "agent-frontmatter", relative(path, root), error))
                    continue
                name = metadata.get("name", path.stem)

            if not isinstance(name, str) or not name:
                findings.append(finding("critical", "agent-name", relative(path, root), "name is missing"))
                continue
            if name != path.stem:
                findings.append(finding("critical", "agent-name", relative(path, root), f"name '{name}' does not match filename"))
            if name in runtime_names:
                findings.append(finding("critical", "agent-name", relative(path, root), f"duplicate role '{name}' in {runtime}"))
            runtime_names.add(name)

        missing = sorted(canonical_names - runtime_names)
        extra = sorted(runtime_names - canonical_names)
        for name in missing:
            findings.append(
                finding(
                    "critical",
                    "agent-runtime-parity",
                    directory,
                    f"{runtime} binding for '{name}' is missing",
                )
            )
        for name in extra:
            findings.append(
                finding(
                    "warning",
                    "agent-runtime-parity",
                    directory,
                    f"{runtime} role '{name}' has no workflow/roles canonical contract",
                )
            )
        names.update(runtime_names)
    return names, findings


def check_runtime_config(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required_entries = {
        "CLAUDE.md": root / "CLAUDE.md",
        "AGENTS.md": root / "AGENTS.md",
        "runtime matrix": root / "workflow" / "rules" / "runtime-adapters.md",
    }
    for label, path in required_entries.items():
        if not path.is_file():
            findings.append(
                finding("critical", "runtime-entry", relative(path, root), f"{label} is missing")
            )

    opencode_config = root / "opencode.json"
    if not opencode_config.is_file():
        findings.append(
            finding("critical", "opencode-config", "opencode.json", "config is missing")
        )
    else:
        try:
            config = json.loads(opencode_config.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(
                finding("critical", "opencode-config", "opencode.json", str(error))
            )
        else:
            skill_permission = config.get("permission", {}).get("skill", {}).get("*")
            if skill_permission != "allow":
                findings.append(
                    finding(
                        "warning",
                        "opencode-skill-permission",
                        "opencode.json",
                        "permission.skill.* should be 'allow'",
                    )
                )
    return findings


PRE_COMMIT_REQUIRED = (
    ".agents/skills/pre-commit-check/SKILL.md",
    ".agents/skills/pre-commit-check/agents/openai.yaml",
    ".claude/commands/pre-commit-check.md",
    ".opencode/commands/pre-commit-check.md",
    "workflow/phases/pre-commit-check.md",
    "workflow/rules/pre-commit-integrity.md",
    "workflow/rules/hook-contract.md",
    "workflow/scripts/pre-commit-check.py",
    "workflow/scripts/configure-git-hooks.sh",
    "workflow/hooks/hook-runner.py",
    ".githooks/pre-commit",
    ".codex/hooks.json",
    ".claude/settings.json",
    ".cursor/hooks.json",
    ".opencode/plugins/harness-hooks.ts",
    "iOS/workflow/phases/pre-commit-check.md",
    "Android/workflow/phases/pre-commit-check.md",
)


def pre_commit_adapter_findings(
    root: Path, platform: str, adapter_path: Path, adapter: dict[str, object]
) -> list[dict[str, str]]:
    label = relative(adapter_path, root) if adapter_path.is_absolute() else adapter_path
    try:
        profile = validate_pre_commit_profile(adapter)
    except RuleProfileError as error:
        return [finding("critical", "pre-commit-adapter", label, str(error))]
    other = "Android/" if platform == "iOS" else "iOS/"
    if other in json.dumps(profile):
        return [finding("critical", "pre-commit-platform-leakage", label, f"profile leaks {other} globs")]
    own = f"{platform}/"
    globs = [
        item for key, value in profile.items() if key not in {"source_suffixes", "tool_globs"}
        for item in value
    ]
    globs.extend(item for values in profile["tool_globs"].values() for item in values)
    if any(not item.startswith(own) for item in globs):
        return [finding("critical", "pre-commit-platform-leakage", label, f"profile globs must remain under {own}")]
    return []


def cursor_hook_findings(config: object, label: str = ".cursor/hooks.json") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(config, dict) or config.get("version") != 1 or not isinstance(config.get("hooks"), dict):
        return [finding("critical", "cursor-hook-schema", label, "version 1 hooks object is required")]
    hooks = config["hooks"]
    if set(hooks) != {"preToolUse", "postToolUse"}:
        findings.append(finding("critical", "cursor-hook-event", label, "exact preToolUse/postToolUse events are required"))
    expected = {"preToolUse": "pre-tool", "postToolUse": "post-edit"}
    for event, runner_event in expected.items():
        entries = hooks.get(event)
        if not isinstance(entries, list) or not entries:
            findings.append(finding("critical", "cursor-hook-schema", label, f"{event} entries are missing"))
            continue
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("failClosed") is not True:
                findings.append(finding("critical", "cursor-hook-fail-closed", label, f"{event} must set failClosed true"))
                continue
            if not isinstance(entry.get("matcher"), str) or not entry["matcher"]:
                findings.append(finding("critical", "cursor-hook-schema", label, f"{event} matcher is missing"))
            command = entry.get("command", "")
            if "workflow/hooks/hook-runner.py" not in command or f"--event {runner_event}" not in command:
                findings.append(finding("critical", "cursor-hook-binding", label, f"{event} runner binding is invalid"))
    return findings


def opencode_hook_findings(
    text: str, label: str = ".opencode/plugins/harness-hooks.ts", *, singular_exists: bool = False
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if singular_exists:
        findings.append(finding("critical", "opencode-hook-location", ".opencode/plugin", "singular plugin directory is not auto-loaded"))
    required = (
        "workflow/hooks/hook-runner.py", "tool.execute.before", "tool.execute.after",
        "async ({ worktree })", "cwd: root", "runHook(worktree",
        "tool_input: output.args", "tool_input: input.args",
        "console.warn", 'report.decision === "warn"',
    )
    for token in required:
        if token not in text:
            findings.append(finding("critical", "opencode-hook-binding", label, f"missing native binding token: {token}"))
    if "/Users/" in text:
        findings.append(finding("critical", "runtime-hook-binding", label, "absolute local path is forbidden"))
    return findings


def hook_runner_findings(text: str, label: str = "workflow/hooks/hook-runner.py") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = (
        "MAX_SHELL_DEPTH", "nested_shell_command",
        're.fullmatch(r"-[A-Za-z]+", token)',
        'Path(segment[index]).name not in {"sh", "bash"}',
        'runtime == "cursor"', '"permission":', '"additional_context":',
        'runtime == "claude"', '"hookSpecificOutput":', '"additionalContext":',
        '"hookEventName": "PreToolUse"', '"hookEventName": "PostToolUse"',
        '"filePath"',
    )
    for token in required:
        if token not in text:
            findings.append(finding("critical", "runtime-hook-schema", label, f"missing runtime behavior token: {token}"))
    return findings


def check_pre_commit_hooks(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for value in PRE_COMMIT_REQUIRED:
        path = root / value
        if not path.is_file():
            findings.append(finding("critical", "pre-commit-files", value, "required pre-commit/hook artifact is missing"))

    hook = root / ".githooks/pre-commit"
    if hook.is_file():
        text = hook.read_text(encoding="utf-8")
        if not os.access(hook, os.X_OK):
            findings.append(finding("critical", "pre-commit-hook", ".githooks/pre-commit", "tracked hook is not executable"))
        if "workflow/scripts/pre-commit-check.py" not in text or "--staged" not in text:
            findings.append(finding("critical", "pre-commit-hook", ".githooks/pre-commit", "hook must invoke the canonical staged gate"))
        if "--no-verify" in text or "git commit" in text:
            findings.append(finding("critical", "pre-commit-hook", ".githooks/pre-commit", "hook must not bypass or perform commit"))

    installer = root / "workflow/scripts/configure-git-hooks.sh"
    if installer.is_file():
        text = installer.read_text(encoding="utf-8")
        if not os.access(installer, os.X_OK):
            findings.append(finding("critical", "hook-installer", relative(installer, root), "installer/check script is not executable"))
        for token in ("--check", "--install", "core.hooksPath", "refusing to overwrite"):
            if token not in text:
                findings.append(finding("critical", "hook-installer", relative(installer, root), f"missing collision-safe token: {token}"))

    for platform in ("iOS", "Android"):
        adapter_path = root / platform / "workflow/platform-contract.json"
        if not adapter_path.is_file():
            continue
        try:
            adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(finding("critical", "pre-commit-adapter", relative(adapter_path, root), str(error)))
            continue
        findings.extend(pre_commit_adapter_findings(root, platform, adapter_path, adapter))

    runner_pointer = "workflow/hooks/hook-runner.py"
    for value in (".codex/hooks.json", ".claude/settings.json", ".cursor/hooks.json"):
        path = root / value
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(finding("critical", "runtime-hook-config", value, str(error)))
            continue
        serialized = json.dumps(data)
        if runner_pointer not in serialized:
            findings.append(finding("critical", "runtime-hook-binding", value, "common hook runner pointer is missing"))
        if "/Users/" in serialized:
            findings.append(finding("critical", "runtime-hook-binding", value, "absolute local path is forbidden"))
        if value == ".cursor/hooks.json":
            findings.extend(cursor_hook_findings(data))
    runner = root / "workflow/hooks/hook-runner.py"
    if runner.is_file():
        runner_text = runner.read_text(encoding="utf-8")
        findings.extend(hook_runner_findings(runner_text, relative(runner, root).as_posix()))
    plugin = root / ".opencode/plugins/harness-hooks.ts"
    if plugin.is_file():
        text = plugin.read_text(encoding="utf-8")
        findings.extend(opencode_hook_findings(
            text, relative(plugin, root).as_posix(),
            singular_exists=(root / ".opencode/plugin").exists(),
        ))
    elif (root / ".opencode/plugin").exists():
        findings.append(finding("critical", "opencode-hook-location", ".opencode/plugin", "singular plugin directory is not auto-loaded"))
    return findings


def check_dispatch_references(
    root: Path, markdown_files: list[Path], agent_names: set[str]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    skill_names = {
        path.name for path in (root / ".agents" / "skills").iterdir() if path.is_dir()
    }
    known = agent_names | skill_names
    for path in markdown_files:
        rel = relative(path, root)
        if not (str(rel).startswith("workflow/") or str(rel).startswith(".agents/")):
            continue
        for role_name in DISPATCH_RE.findall(path.read_text(encoding="utf-8")):
            if role_name not in known:
                findings.append(finding("warning", "dead-dispatch-ref", rel, role_name))
    return findings


def check_platform_contract(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    roots = {path.name.lower(): path for path in root.iterdir() if path.is_dir()}
    for name in ("ios", "android"):
        platform_root = roots.get(name)
        if platform_root is None:
            findings.append(finding("critical", "platform-root", name, "platform directory is missing"))
        elif not (platform_root / "AGENTS.md").is_file():
            findings.append(finding("warning", "platform-entry", platform_root.name, "AGENTS.md is missing"))

    scope_rule = root / "workflow" / "rules" / "platform-scope.md"
    if not scope_rule.is_file():
        findings.append(finding("critical", "platform-scope", "workflow/rules/platform-scope.md", "scope contract is missing"))
    else:
        text = scope_rule.read_text(encoding="utf-8").lower()
        for token in ("ios", "android", "cross-platform"):
            if token not in text:
                findings.append(finding("critical", "platform-scope", relative(scope_rule, root), f"'{token}' is missing"))
    return findings


def check_specification_layers(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = (
        "workflow/rules/specification-layers.md",
        "workflow/phases/brainstorming.md",
        "workflow/phases/discovery.md",
        "workflow/phases/elaborate.md",
        "workflow/templates/product-concept.md",
        "workflow/templates/product-brief.md",
        "workflow/templates/product-ux.md",
        "workflow/templates/product-spec.md",
        "workflow/templates/platform-implementation-spec.md",
        "specs/product/README.md",
        "iOS/specs/README.md",
        "Android/specs/README.md",
    )
    for value in required:
        if not (root / value).is_file():
            findings.append(
                finding("critical", "specification-layers", value, "required file is missing")
            )

    rule = root / "workflow/rules/specification-layers.md"
    if rule.is_file():
        text = rule.read_text(encoding="utf-8")
        for token in (
            "specs/product/<feature>/",
            "iOS/specs/<feature>/changes/<change-id>/",
            "Android/specs/<feature>/changes/<change-id>/",
            "ux.md",
            "Product approval: APPROVED",
            "product-backed",
            "technical-only",
            "Product impact assessment: NONE",
            "READY",
        ):
            if token not in text:
                findings.append(
                    finding(
                        "critical",
                        "specification-layers",
                        relative(rule, root),
                        f"required boundary token is missing: {token}",
                    )
                )
    content_requirements = {
        "workflow/phases/discovery.md": (
            "Draft UX impact",
            "screen/flow map",
            "accessibility/localization",
        ),
        "workflow/phases/elaborate.md": (
            "product-ux.md",
            "review lenses",
            "Product approval: APPROVED",
            "DRAFT / PENDING APPROVAL",
        ),
        "workflow/templates/product-ux.md": (
            "User Journey",
            "Flow and Screen Impact",
            "Accessibility and Localization",
            "Shared Design-System Intent",
        ),
        "workflow/templates/product-spec.md": (
            "Product approval",
            "Approval evidence",
            "UX artifact",
            "Product Review Lenses",
        ),
        "workflow/templates/platform-implementation-spec.md": (
            "Change type",
            "product-backed | technical-only",
            "Shared product spec",
            "Product Impact Assessment",
            "NONE | PRESENT | UNCERTAIN",
        ),
        "iOS/specs/README.md": (
            "product-backed",
            "technical-only",
            "Product impact assessment: NONE",
        ),
        "Android/specs/README.md": (
            "product-backed",
            "technical-only",
            "Product impact assessment: NONE",
        ),
    }
    for value, tokens in content_requirements.items():
        path = root / value
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(
                    finding(
                        "critical",
                        "specification-layers",
                        value,
                        f"required product gate is missing: {token}",
                    )
                )
    return findings


def check_implementation_lifecycle(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = (
        "workflow/phases/implement.md",
        "workflow/phases/verify.md",
        "workflow/phases/archive.md",
        "workflow/rules/verification-evidence.md",
        "workflow/rules/archive-lifecycle.md",
        "workflow/roles/implementation-discovery.md",
        "workflow/roles/verifier.md",
        "workflow/templates/product-archive-request.json",
        "workflow/scripts/validate-implementation-scope.py",
        "workflow/scripts/capture-verification-state.py",
        "workflow/scripts/archive-change.py",
        "iOS/workflow/phases/implement.md",
        "iOS/workflow/phases/verify.md",
        "iOS/workflow/phases/archive.md",
    )
    for value in required:
        if not (root / value).is_file():
            findings.append(finding("critical", "implementation-lifecycle", value, "required file is missing"))

    lifecycle = root / "workflow/rules/platform-change-lifecycle.md"
    if lifecycle.is_file():
        text = lifecycle.read_text(encoding="utf-8")
        for token in (
            "changes/<change-id>/", "archive/<YYYY-MM-DD-change-id>/",
            "draft → specified → planned → implementing → verified → archived",
            "tasks_done", "verification_state", "no legacy fallback",
        ):
            if token not in text:
                findings.append(finding("critical", "implementation-lifecycle", relative(lifecycle, root), f"required token is missing: {token}"))

    adapter_path = root / "iOS/workflow/platform-contract.json"
    if adapter_path.is_file():
        try:
            adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(finding("critical", "implementation-adapter", relative(adapter_path, root), str(error)))
        else:
            for key in (
                "active_changes_namespace", "archive_namespace", "production_roots",
                "protected_roots", "production_exclusions", "rule_files",
                "context_file_suffixes", "context_excluded_directories",
                "context_always_include_globs", "scope_task_checks",
            ):
                if key not in adapter:
                    findings.append(finding("critical", "implementation-adapter", relative(adapter_path, root), f"missing field: {key}"))

    expected_capabilities = {
        "iOS": ["propose", "plan", "implement", "verify", "archive-implementation"],
        "Android": ["propose", "plan", "implement"],
    }
    for platform, expected in expected_capabilities.items():
        path = root / platform / "workflow/platform-contract.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            capabilities = validate_capabilities(data)
            validate_profiles(root, data)
        except (OSError, json.JSONDecodeError, RuleProfileError) as error:
            findings.append(finding("critical", "implementation-capabilities", relative(path, root), str(error)))
            continue
        if capabilities != expected:
            findings.append(finding("critical", "implementation-capabilities", relative(path, root), f"expected exact capabilities: {expected}"))
        serialized = json.dumps(data)
        other = "Android/" if platform == "iOS" else "iOS/"
        if other in serialized:
            findings.append(finding("critical", "implementation-capabilities", relative(path, root), f"adapter leaks {other} rules"))

    for name in ("propose", "plan", "implement", "verify", "archive"):
        metadata = root / ".agents/skills" / name / "agents/openai.yaml"
        if metadata.is_file() and "allow_implicit_invocation: false" not in metadata.read_text(encoding="utf-8"):
            findings.append(finding("critical", "manual-only-skill", relative(metadata, root), "allow_implicit_invocation must be false"))
    return findings


ANDROID_REQUIRED_RULES = {
    "Android/workflow/rules/architecture.md",
    "Android/workflow/rules/architecture/data-layer.md",
    "Android/workflow/rules/architecture/ui-layer.md",
    "Android/workflow/rules/architecture/domain-layer.md",
    "Android/workflow/rules/architecture/dependency-injection.md",
    "Android/workflow/rules/architecture/modularization.md",
    "Android/workflow/rules/kotlin-style.md",
    "Android/workflow/rules/coroutines-flows.md",
    "Android/workflow/rules/compose.md",
    "Android/workflow/rules/gradle-build.md",
    "Android/workflow/rules/android-pitfalls.md",
    "Android/workflow/rules/unit-testing.md",
    "Android/workflow/rules/ui-testing.md",
    "Android/workflow/rules/accessibility.md",
    "Android/workflow/rules/ui-design-system.md",
    "Android/workflow/rules/localization.md",
    "Android/workflow/rules/emulator.md",
    "Android/workflow/rules/multiplatform.md",
}

ANDROID_FIXED_ASSUMPTIONS = (
    "kotlin 1.9+", "85% coverage", "mandatory compose", "mandatory hilt",
    "always use hilt", "always use compose", "./gradlew build",
)
ANDROID_PLATFORM_LEAKAGE = re.compile(r"\b(?:Swift|Xcode|UIKit|SwiftUI|Apple SDK)\b", re.IGNORECASE)


def android_profile_findings(
    root: Path, adapter_path: Path, adapter: dict[str, object]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    label = relative(adapter_path, root)
    try:
        catalog, phases, scopes = validate_profiles(root, adapter)
    except RuleProfileError as error:
        return [finding("critical", "android-engineering-profiles", label, str(error))]
    actual_rules = {
        path.relative_to(root).as_posix()
        for path in (root / "Android/workflow/rules").rglob("*.md")
    }
    missing_files = sorted(ANDROID_REQUIRED_RULES - actual_rules)
    uncatalogued = sorted(actual_rules - set(catalog))
    if missing_files:
        findings.append(finding("critical", "android-engineering-rules", label, f"required Android rules missing: {', '.join(missing_files)}"))
    if uncatalogued:
        findings.append(finding("critical", "android-engineering-profiles", label, f"Android rules missing from catalog: {', '.join(uncatalogued)}"))
    if list(phases) != ["propose", "plan", "implement"]:
        findings.append(finding("critical", "android-engineering-profiles", label, "Android phases must be exact propose/plan/implement"))
    if adapter.get("scope_dependencies", {}).get("compose") != ["ui"]:
        findings.append(finding("critical", "android-engineering-dependency", label, "compose scope must require ui"))
    if "Android/workflow/rules/compose.md" in scopes.get("ui", []):
        findings.append(finding("critical", "android-engineering-dependency", label, "ui must not imply compose"))
    if "Android/workflow/rules/multiplatform.md" in scopes.get("application", []) or "Android/workflow/rules/multiplatform.md" in scopes.get("ui", []):
        findings.append(finding("critical", "android-engineering-dependency", label, "multiplatform must remain evidence-selected"))
    checks = adapter.get("scope_task_checks", {})
    required_checks = {
        "ui": {"emulator", "accessibility", "design-system"},
        "compose": {"Compose state"}, "multiplatform": {"source set"},
        "concurrency": {"cancellation", "lifecycle"}, "gradle": {"Gradle task"},
    }
    for scope, expected in required_checks.items():
        if not expected <= set(checks.get(scope, [])):
            findings.append(finding("critical", "android-engineering-dependency", label, f"scope_task_checks.{scope} misses obligations"))
    return findings


def android_assumption_findings(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in (root / "Android/workflow/rules").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()
        for token in ANDROID_FIXED_ASSUMPTIONS:
            if token.casefold() in lowered:
                findings.append(finding("critical", "android-fixed-assumption", relative(path, root), f"fixed source assumption: {token}"))
        if ANDROID_PLATFORM_LEAKAGE.search(text):
            findings.append(finding("critical", "android-platform-leakage", relative(path, root), "Android rule names an iOS-only technology"))
    return findings


def self_test_android_lint(root: Path) -> int:
    path = root / "Android/workflow/platform-contract.json"
    adapter = json.loads(path.read_text(encoding="utf-8"))
    assert android_profile_findings(root, path, adapter) == []

    missing_catalog = copy.deepcopy(adapter)
    missing_catalog["rule_files"].remove("Android/workflow/rules/compose.md")
    assert any(
        item["check"] == "android-engineering-profiles"
        for item in android_profile_findings(root, path, missing_catalog)
    )

    missing_mapping = copy.deepcopy(adapter)
    missing_mapping["scope_rule_profiles"]["compose"] = ["Android/workflow/rules/ui-testing.md"]
    assert any(
        item["check"] == "android-engineering-profiles"
        for item in android_profile_findings(root, path, missing_mapping)
    )

    disabled_verify = copy.deepcopy(adapter)
    disabled_verify["phase_rule_profiles"]["verify"] = ["workflow/rules/test-execution.md"]
    assert any(
        item["check"] == "android-engineering-profiles"
        for item in android_profile_findings(root, path, disabled_verify)
    )

    broken_compose = copy.deepcopy(adapter)
    broken_compose["scope_dependencies"] = {}
    assert any(
        item["check"] == "android-engineering-dependency"
        for item in android_profile_findings(root, path, broken_compose)
    )

    with tempfile.TemporaryDirectory() as tmp:
        fixture_root = Path(tmp).resolve()
        fixture_rule = fixture_root / "Android/workflow/rules/fixed.md"
        fixture_rule.parent.mkdir(parents=True)
        fixture_rule.write_text("Project requires Kotlin 1.9+ and 85% coverage.\n", encoding="utf-8")
        assert len(android_assumption_findings(fixture_root)) == 2

    ios_path = root / "iOS/workflow/platform-contract.json"
    ios_adapter = json.loads(ios_path.read_text(encoding="utf-8"))
    assert pre_commit_adapter_findings(root, "iOS", ios_path, ios_adapter) == []
    assert pre_commit_adapter_findings(root, "Android", path, adapter) == []
    missing_pre_commit = copy.deepcopy(adapter)
    missing_pre_commit.pop("pre_commit")
    assert any(
        item["check"] == "pre-commit-adapter"
        for item in pre_commit_adapter_findings(root, "Android", path, missing_pre_commit)
    )
    leaked_pre_commit = copy.deepcopy(adapter)
    leaked_pre_commit["pre_commit"]["generated_globs"].append("iOS/**/build/**")
    assert any(
        item["check"] == "pre-commit-platform-leakage"
        for item in pre_commit_adapter_findings(root, "Android", path, leaked_pre_commit)
    )
    with tempfile.TemporaryDirectory() as tmp:
        missing_root = Path(tmp).resolve()
        missing = check_pre_commit_hooks(missing_root)
        assert any(item["file"] == ".githooks/pre-commit" for item in missing)
        assert any(item["file"] == ".claude/commands/pre-commit-check.md" for item in missing)
    cursor_path = root / ".cursor/hooks.json"
    cursor_config = json.loads(cursor_path.read_text(encoding="utf-8"))
    assert cursor_hook_findings(cursor_config) == []
    cursor_bad_event = copy.deepcopy(cursor_config)
    cursor_bad_event["hooks"]["beforeFileEdit"] = cursor_bad_event["hooks"].pop("preToolUse")
    assert any(item["check"] == "cursor-hook-event" for item in cursor_hook_findings(cursor_bad_event))
    cursor_open = copy.deepcopy(cursor_config)
    cursor_open["hooks"]["preToolUse"][0].pop("failClosed")
    assert any(item["check"] == "cursor-hook-fail-closed" for item in cursor_hook_findings(cursor_open))
    opencode_path = root / ".opencode/plugins/harness-hooks.ts"
    opencode_text = opencode_path.read_text(encoding="utf-8")
    assert opencode_hook_findings(opencode_text) == []
    assert any(item["check"] == "opencode-hook-location" for item in opencode_hook_findings(opencode_text, singular_exists=True))
    assert any(item["check"] == "opencode-hook-binding" for item in opencode_hook_findings(opencode_text.replace("tool_input: output.args", "tool_input: input")))
    assert any(item["check"] == "opencode-hook-binding" for item in opencode_hook_findings(opencode_text.replace("async ({ worktree })", "async ({ directory })")))
    assert any(item["check"] == "opencode-hook-binding" for item in opencode_hook_findings(opencode_text.replace("tool_input: input.args", "tool_input: output.args")))
    assert any(item["check"] == "opencode-hook-binding" for item in opencode_hook_findings(opencode_text.replace("console.warn", "void")))
    runner_text = (root / "workflow/hooks/hook-runner.py").read_text(encoding="utf-8")
    assert hook_runner_findings(runner_text) == []
    assert any(item["check"] == "runtime-hook-schema" for item in hook_runner_findings(runner_text.replace("nested_shell_command", "removed_shell_inspection")))
    for start in (root, root / "iOS", root / "Android"):
        result = subprocess.run(
            ["python3", str(root / "workflow/hooks/hook-runner.py"), "--runtime", "opencode", "--event", "pre-tool", "--root", str(root)],
            cwd=start, input=json.dumps({"tool": "write", "args": {"filePath": "workflow/README.md"}}),
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, f"OpenCode worktree-root payload failed from {start}: {result.stdout} {result.stderr}"
    for script in (
        "workflow/scripts/pre-commit-check.py",
        "workflow/hooks/hook-runner.py",
        "workflow/scripts/configure-git-hooks.sh",
    ):
        command = ["bash", script, "--self-test"] if script.endswith(".sh") else ["python3", script, "--self-test"]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        assert result.returncode == 0, f"{script} self-test failed: {result.stdout} {result.stderr}"
    print("harness-lint self-test: PASS (Android corpus/profile + pre-commit/hook mutations)")
    return 0


def check_engineering_rule_profiles(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = (
        "workflow/rules/coding-standards.md", "workflow/rules/code-comments.md",
        "workflow/rules/tdd-first.md", "workflow/rules/test-execution.md",
        "workflow/rules/verification-matrix.md", "workflow/rules/git-conventions.md",
        "workflow/rules/branching.md", "workflow/rules/developer-experience.md",
        "workflow/scripts/test-watchdog.sh",
        "iOS/workflow/rules/swift-style.md", "iOS/workflow/rules/app-development.md",
        "iOS/workflow/rules/package-development.md", "iOS/workflow/rules/simulator.md",
        "iOS/workflow/rules/performance.md",
        "iOS/workflow/rules/performance/app-launch.md",
        "iOS/workflow/rules/performance/concurrency.md",
        "iOS/workflow/rules/performance/measure-first.md",
        "iOS/workflow/rules/performance/memory.md",
        "iOS/workflow/rules/performance/networking.md",
        "iOS/workflow/rules/performance/profiling.md",
        "iOS/workflow/rules/performance/swiftui-rendering.md",
    )
    for value in required:
        path = root / value
        if not path.is_file():
            findings.append(finding("critical", "engineering-rules", value, "required engineering canon is missing"))

    adapter_path = root / "iOS/workflow/platform-contract.json"
    if not adapter_path.is_file():
        return findings
    try:
        adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        catalog, phases, scopes = validate_profiles(root, adapter)
    except (json.JSONDecodeError, RuleProfileError) as error:
        findings.append(finding("critical", "engineering-profiles", relative(adapter_path, root), str(error)))
        return findings
    if tuple(phases) != PHASES:
        findings.append(finding("critical", "engineering-profiles", relative(adapter_path, root), "phase profile order/keys are not canonical"))
    ios_rules = {
        path.relative_to(root).as_posix()
        for path in (root / "iOS/workflow/rules").rglob("*.md")
    }
    missing_catalog = sorted(ios_rules - set(catalog))
    if missing_catalog:
        findings.append(finding("critical", "engineering-profiles", relative(adapter_path, root), f"iOS rules missing from catalog: {', '.join(missing_catalog)}"))
    dependencies = {
        "ui": {
            "iOS/workflow/rules/accessibility.md",
            "iOS/workflow/rules/ui-design-system.md",
            "iOS/workflow/rules/ui-testing.md",
            "iOS/workflow/rules/ui-test-spec.md",
            "iOS/workflow/rules/simulator.md",
            "iOS/workflow/rules/architecture/mvvm.md",
        },
        "concurrency": {
            "iOS/workflow/rules/swift-concurrency.md",
            "iOS/workflow/rules/performance/concurrency.md",
        },
        "networking": {"iOS/workflow/rules/performance/networking.md"},
    }
    for scope, expected in dependencies.items():
        if not expected <= set(scopes.get(scope, [])):
            findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), f"scope {scope} misses required rules"))
    performance_expected = {
        "iOS/workflow/rules/performance.md",
        "iOS/workflow/rules/performance/measure-first.md",
        "iOS/workflow/rules/performance/profiling.md",
    }
    if set(scopes.get("performance", [])) != performance_expected:
        findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), "performance base must remain selective"))
    if "iOS/workflow/rules/architecture/mvvm.md" in scopes.get("application", []):
        findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), "MVVM belongs to ui, not application base"))
    if "iOS/workflow/rules/unit-testing.md" in phases.get("verify", []):
        findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), "unit testing must not load for every verify scope"))
    for scope, rule in (
        ("startup", "iOS/workflow/rules/performance/app-launch.md"),
        ("memory", "iOS/workflow/rules/performance/memory.md"),
        ("rendering", "iOS/workflow/rules/performance/swiftui-rendering.md"),
    ):
        if scopes.get(scope) != [rule]:
            findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), f"{scope} topic profile is invalid"))
    if "iOS/workflow/rules/localization.md" in scopes.get("ui", []):
        findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), "ui must not imply the separate localization scope"))
    suffixes = adapter.get("context_file_suffixes")
    if not isinstance(suffixes, list) or not suffixes or not all(
        isinstance(item, str) and re.fullmatch(r"\.[a-z0-9]+", item) for item in suffixes
    ):
        findings.append(finding("critical", "engineering-profiles", relative(adapter_path, root), "context_file_suffixes is invalid"))
    if not isinstance(adapter.get("context_excluded_directories"), list) or not isinstance(adapter.get("context_always_include_globs"), list):
        findings.append(finding("critical", "engineering-profiles", relative(adapter_path, root), "adapter-owned context exclusions/globs are missing"))
    task_checks = adapter.get("scope_task_checks")
    if not isinstance(task_checks, dict) or task_checks.get("ui") != adapter.get("ui_task_checks") or task_checks.get("localization") != ["localization"]:
        findings.append(finding("critical", "engineering-profile-dependency", relative(adapter_path, root), "scope_task_checks must preserve exact UI and conditional localization gates"))
    required_task_checks = {
        "package": {"package consumer", "package build"},
        "networking": {"cache policy", "retry policy"},
        "concurrency": {"cancellation", "isolation"},
        "performance": {"performance budget"},
        "startup": {"launch budget"},
    }
    for scope, expected_checks in required_task_checks.items():
        if not isinstance(task_checks, dict) or not expected_checks <= set(task_checks.get(scope, [])):
            findings.append(finding(
                "critical", "engineering-profile-dependency", relative(adapter_path, root),
                f"scope_task_checks.{scope} misses deterministic task obligations",
            ))

    template = root / "workflow/templates/platform-meta.json"
    if template.is_file():
        text = template.read_text(encoding="utf-8")
        for token in ('"engineering_scopes"', '"applicable_rule_files"', '"rule_selection_snapshot"'):
            if token not in text:
                findings.append(finding("critical", "engineering-meta", relative(template, root), f"missing field: {token}"))
    selection_template = root / "workflow/templates/platform-rule-selection.json"
    if not selection_template.is_file():
        findings.append(finding("critical", "engineering-meta", "workflow/templates/platform-rule-selection.json", "planned selection snapshot template is missing"))
    wiring = {
        "workflow/phases/propose.md": ("engineering_scopes", "applicable_rule_files", "--phase propose"),
        "workflow/phases/plan.md": ("--phase plan", "watchdog", "performance", "rule-selection.json", "scope_task_checks"),
        "workflow/phases/implement.md": ("--phase implement", "test-watchdog.sh", "TDD"),
        "workflow/phases/verify.md": ("--phase verify", "verification matrix", "UNKNOWN"),
    }
    for value, tokens in wiring.items():
        path = root / value
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(finding("critical", "engineering-wiring", value, f"missing token: {token}"))

    forbidden = (
        "jour" + "io", "design_system_" + "helper", "Tui" + "st",
        "Swin" + "ject", "Mae" + "stro", "Liquid " + "Glass",
    )
    scan_roots = [
        root / "workflow/rules", root / "iOS/workflow/rules",
        root / "Android/workflow/rules",
    ]
    for scan_root in scan_roots:
        for path in scan_root.rglob("*.md"):
            lowered = path.read_text(encoding="utf-8").casefold()
            for token in forbidden:
                if token.casefold() in lowered:
                    findings.append(finding("critical", "source-assumption", relative(path, root), f"forbidden source-only assumption: {token}"))
    common_neutral_files = [root / value for value in required if value.startswith("workflow/rules/")]
    common_neutral_files.append(root / "workflow/phases/implement.md")
    platform_tokens = re.compile(
        r"\b(?:Swift|Xcode|UIKit|SwiftUI|Apple SDK|Simulator|Kotlin|Gradle|Android SDK)\b",
        re.IGNORECASE,
    )
    for common_path in common_neutral_files:
        if common_path.is_file() and platform_tokens.search(common_path.read_text(encoding="utf-8")):
            findings.append(finding(
                "critical", "common-platform-leakage", relative(common_path, root),
                "platform-neutral common canon names a platform-only technology",
            ))
    context_script = root / "workflow/scripts/find-platform-context.py"
    if context_script.is_file():
        script_text = context_script.read_text(encoding="utf-8")
        for token in ('".sw' + 'ift"', '".xcode' + 'proj"', '".kot' + 'lin"', '".gra' + 'dle"'):
            if token in script_text:
                findings.append(finding("critical", "common-platform-leakage", relative(context_script, root), f"context suffix must be adapter-owned: {token}"))
    android_adapter_path = root / "Android/workflow/platform-contract.json"
    if not android_adapter_path.is_file():
        findings.append(finding("critical", "android-engineering-profiles", relative(android_adapter_path, root), "Android adapter is missing"))
    else:
        try:
            android_adapter = json.loads(android_adapter_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(finding("critical", "android-engineering-profiles", relative(android_adapter_path, root), str(error)))
        else:
            findings.extend(android_profile_findings(root, android_adapter_path, android_adapter))
    findings.extend(android_assumption_findings(root))
    for runtime in (".claude", ".opencode"):
        for command in ("propose", "plan", "implement"):
            path = root / runtime / "commands" / f"{command}.md"
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            if "Android" not in text or "поддержан iOS" in text:
                findings.append(finding("critical", "android-runtime-capability", relative(path, root), f"{command} command must describe Android capability support"))
        verify_path = root / runtime / "commands/verify.md"
        verify_text = verify_path.read_text(encoding="utf-8") if verify_path.is_file() else ""
        if "Android" not in verify_text or "capability" not in verify_text:
            findings.append(finding("critical", "android-runtime-capability", relative(verify_path, root), "verify command must describe Android capability blocker"))
    return findings


def check_naming(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for area in (
        root / "workflow",
        root / "process",
        root / ".agents",
        root / ".codex",
        root / ".claude",
        root / ".cursor",
        root / ".opencode",
    ):
        if not area.exists():
            continue
        for path in iter_files(area, (".md", ".py", ".toml")):
            if path.name in {"README.md", "SKILL.md", "AGENTS.md"}:
                continue
            if not NAME_RE.match(path.name):
                findings.append(finding("warning", "naming", relative(path, root), "use kebab-case or SCREAMING_SNAKE"))
    return findings


def grade(findings: list[dict[str, str]]) -> str:
    critical = sum(item["severity"] == "critical" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    if critical >= 3:
        return "F"
    if critical:
        return "D"
    if warnings > 10:
        return "C"
    if warnings:
        return "B"
    return "A"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--warn-as-error", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    root = repository_root()
    if args.self_test:
        return self_test_android_lint(root)
    markdown_files = iter_files(root, (".md",))
    findings: list[dict[str, str]] = []
    findings.extend(check_links(root, markdown_files))
    findings.extend(check_skills(root))
    agent_names, agent_findings = read_agents(root)
    findings.extend(agent_findings)
    findings.extend(check_runtime_config(root))
    findings.extend(check_pre_commit_hooks(root))
    findings.extend(check_dispatch_references(root, markdown_files, agent_names))
    findings.extend(check_platform_contract(root))
    findings.extend(check_specification_layers(root))
    findings.extend(check_implementation_lifecycle(root))
    findings.extend(check_engineering_rule_profiles(root))
    findings.extend(check_naming(root))
    findings.sort(key=lambda item: (item["severity"], item["check"], item["file"]))

    result = {
        "grade": grade(findings),
        "critical": sum(item["severity"] == "critical" for item in findings),
        "warnings": sum(item["severity"] == "warning" for item in findings),
        "findings": findings,
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Harness lint: grade {result['grade']} ({result['critical']} critical, {result['warnings']} warnings)")
        for item in findings:
            print(f"[{item['severity'].upper()}] {item['check']} {item['file']}: {item['detail']}")

    if result["critical"] or (args.warn_as_error and result["warnings"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
