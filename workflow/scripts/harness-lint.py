#!/usr/bin/env python3
"""Deterministic structural checks for the repository workflow harness."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import unquote

from platform_rule_profiles import (
    ARTIFACT_LANGUAGE_RULE,
    COMMON_MODULARITY_RULE,
    LEGACY_REGISTRY_PATH,
    PHASES,
    RuleProfileError,
    load_legacy_registry,
    legacy_package_hashes,
    resolve_package_contract_version,
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


def load_docs_checker(root: Path):
    path = root / "workflow/scripts/harness-docs.py"
    if not path.is_file():
        return None, "workflow/scripts/harness-docs.py is missing"
    spec = importlib.util.spec_from_file_location("harness_docs", path)
    if spec is None or spec.loader is None:
        return None, "harness-docs.py cannot be loaded"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (ImportError, OSError, SyntaxError, ValueError) as error:
        return None, str(error)
    return module, None


def check_repository_docs(root: Path) -> list[dict[str, str]]:
    module, error = load_docs_checker(root)
    if error:
        return [finding("critical", "repository-documentation", "workflow/scripts/harness-docs.py", error)]
    result = module.check_repository(root)
    if result.get("status") == "PASS":
        return []
    return [
        finding("critical", "repository-documentation", "README.md | workflow.md | deep-info.md", detail)
        for detail in result.get("errors", ["documentation checker returned no diagnostics"])
    ]


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
    "workflow/scripts/git_change_paths.py",
    "workflow/scripts/platform_path_ownership.py",
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
        if "workflow/scripts/pre-commit-check.py" not in text or "--staged" not in text or "--hook" not in text:
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
            "product-spec-review.md",
            "Product approval: APPROVED",
            "DRAFT / PENDING APPROVAL",
            "validate-product-spec.py check",
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
            "Product review receipt",
            "review-verdicts.json",
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
        "Android/workflow/phases/verify.md",
        "Android/workflow/phases/archive.md",
    )
    for value in required:
        if not (root / value).is_file():
            findings.append(finding("critical", "implementation-lifecycle", value, "required file is missing"))

    validator = root / "workflow/scripts/validate-platform-change.py"
    if validator.is_file():
        text = validator.read_text(encoding="utf-8")
        for token in (
            'repo / "workflow/rules/verification-evidence.md"',
            'repo / "workflow/phases/verify.md"',
            'platform_root / "workflow/phases/verify.md"',
            "required terminal verification input is missing",
        ):
            if token not in text:
                findings.append(finding("critical", "terminal-verification-inputs", relative(validator, root), f"required token is missing: {token}"))

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
        "Android": ["propose", "plan", "implement", "verify", "archive-implementation"],
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
ANDROID_TERMINAL_CONTRACTS = {
    "Android/workflow/phases/verify.md": (
        "Не предполагать", "watchdog", "PASS|FAIL|UNKNOWN",
        "android-build-diagnostician", "production",
    ),
    "Android/workflow/phases/archive.md": (
        "archive_namespace", "dry-run", "receipt", "tombstone", "rollback",
        "Shared product package",
    ),
}


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
    if list(phases) != ["propose", "plan", "implement", "verify"]:
        findings.append(finding("critical", "android-engineering-profiles", label, "Android phases must be exact propose/plan/implement/verify"))
    expected_verify = [
        "workflow/rules/test-execution.md",
        ARTIFACT_LANGUAGE_RULE,
        "workflow/rules/verification-matrix.md",
        COMMON_MODULARITY_RULE,
        "Android/workflow/rules/architecture/modularization.md",
    ]
    if phases.get("verify") != expected_verify:
        findings.append(finding("critical", "android-engineering-profiles", label, "Android verify profile must preserve the exact compatibility pair plus modularity contracts"))
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
        "module": {"module boundary", "module build", "public contract", "consumer integration", "dependency graph", "app-shell wiring"},
    }
    for scope, expected in required_checks.items():
        if not expected <= set(checks.get(scope, [])):
            findings.append(finding("critical", "android-engineering-dependency", label, f"scope_task_checks.{scope} misses obligations"))
    return findings


def modularity_profile_findings(
    root: Path, adapter_path: Path, adapter: dict[str, object]
) -> list[dict[str, str]]:
    label = relative(adapter_path, root)
    try:
        _catalog, phases, scopes = validate_profiles(root, adapter)
    except RuleProfileError as error:
        return [finding("critical", "cross-platform-modularity", label, str(error))]
    config = adapter.get("modularity")
    if not isinstance(config, dict):
        return [finding("critical", "cross-platform-modularity", label, "modularity config is missing")]
    platform_rule = str(config.get("platform_rule", ""))
    findings: list[dict[str, str]] = []
    for phase in PHASES:
        rules = phases.get(phase, [])
        for rule in (ARTIFACT_LANGUAGE_RULE, COMMON_MODULARITY_RULE, platform_rule):
            if rule not in rules:
                findings.append(finding(
                    "critical", "cross-platform-modularity", label,
                    f"phase_rule_profiles.{phase} misses mandatory rule: {rule}",
                ))
    isolation_scope = str(config.get("isolation_scope", ""))
    if isolation_scope not in scopes:
        findings.append(finding(
            "critical", "cross-platform-modularity", label,
            "adapter modularity isolation scope is not a known scope",
        ))
    required_checks = {
        "public contract", "consumer integration", "dependency graph", "app-shell wiring",
    }
    checks = adapter.get("scope_task_checks", {})
    scope_checks = set(checks.get(isolation_scope, [])) if isinstance(checks, dict) else set()
    if not required_checks <= scope_checks:
        findings.append(finding(
            "critical", "cross-platform-modularity", label,
            f"scope_task_checks.{isolation_scope} misses modularity obligations",
        ))
    return findings


def legacy_registry_findings(root: Path) -> list[dict[str, str]]:
    label = LEGACY_REGISTRY_PATH
    try:
        entries = load_legacy_registry(root)
    except RuleProfileError as error:
        return [finding("critical", "modularity-v0-registry", label, str(error))]
    findings: list[dict[str, str]] = []
    adapters: dict[str, dict[str, object]] = {}
    for adapter_path in sorted(root.glob("*/workflow/platform-contract.json")):
        try:
            adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        platform_name = adapter.get("platform_name")
        if isinstance(platform_name, str):
            adapters[platform_name] = adapter
    for entry in entries:
        package = root / str(entry["package_path"])
        if not package.exists():
            continue
        if (package / "ARCHIVED.md").is_file():
            continue
        meta_path = package / "meta.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            findings.append(finding("critical", "modularity-v0-registry", relative(meta_path, root), f"active anchored meta is invalid: {error}"))
            continue
        if meta.get("status") == "archived":
            continue
        adapter = adapters.get(str(entry["platform"]))
        if adapter is None:
            findings.append(finding("critical", "modularity-v0-registry", label, f"active anchor adapter is missing: {entry['platform']}"))
            continue
        try:
            version = resolve_package_contract_version(root, adapter, meta, package, "implement")
        except RuleProfileError as error:
            findings.append(finding("critical", "modularity-v0-registry", relative(package, root), str(error)))
        else:
            if version != 0:
                findings.append(finding("critical", "modularity-v0-registry", relative(package, root), "registered active package must resolve legacy v0"))
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


def android_terminal_addendum_findings(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for raw, tokens in ANDROID_TERMINAL_CONTRACTS.items():
        path = root / raw
        if not path.is_file():
            findings.append(finding("critical", "android-terminal-addendum", raw, "required Android terminal addendum is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(finding("critical", "android-terminal-addendum", relative(path, root), f"missing invariant: {token}"))
        if re.search(r"\b(?:Swift|SwiftUI|UIKit|Xcode|Apple SDK|Simulator)\b", text, re.IGNORECASE):
            findings.append(finding("critical", "android-platform-leakage", relative(path, root), "Android terminal addendum names an iOS-only technology"))
        if re.search(r"(?:\./gradlew|\bgradle\s+(?:build|test|lint)|\bconnectedAndroidTest\b)", text, re.IGNORECASE):
            findings.append(finding("critical", "android-fixed-assumption", relative(path, root), "Android terminal addendum hardcodes a Gradle command/task"))
    return findings


def self_test_android_lint(root: Path) -> int:
    path = root / "Android/workflow/platform-contract.json"
    adapter = json.loads(path.read_text(encoding="utf-8"))
    assert android_profile_findings(root, path, adapter) == []
    assert modularity_profile_findings(root, path, adapter) == []

    ios_path = root / "iOS/workflow/platform-contract.json"
    ios_adapter = json.loads(ios_path.read_text(encoding="utf-8"))
    assert modularity_profile_findings(root, ios_path, ios_adapter) == []
    assert legacy_registry_findings(root) == []

    registry_source = json.loads((root / LEGACY_REGISTRY_PATH).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        fixture_root = Path(tmp).resolve()
        registry_path = fixture_root / LEGACY_REGISTRY_PATH
        registry_path.parent.mkdir(parents=True)
        for mutation in ("absolute-path", "duplicate", "bad-hash", "normalization"):
            candidate = copy.deepcopy(registry_source)
            if mutation == "absolute-path":
                candidate["packages"][0]["package_path"] = "/tmp/escape"
            elif mutation == "duplicate":
                candidate["packages"].append(copy.deepcopy(candidate["packages"][0]))
            elif mutation == "bad-hash":
                candidate["packages"][0]["hashes"]["design_sha256"] = "not-a-hash"
            else:
                candidate["task_normalization"]["ignored_field_values"].append("Paths")
            registry_path.write_text(json.dumps(candidate), encoding="utf-8")
            try:
                load_legacy_registry(fixture_root)
                raise AssertionError(f"legacy registry mutation passed: {mutation}")
            except RuleProfileError:
                pass

    with tempfile.TemporaryDirectory() as tmp:
        fixture_root = Path(tmp).resolve()
        copied_package = fixture_root / "iOS/specs/forged-v0/changes/forged-v0"
        shutil.copytree(
            root / "iOS/specs/client-bootstrap/changes/initial-scaffold",
            copied_package,
        )
        copied_meta_path = copied_package / "meta.json"
        copied_meta = json.loads(copied_meta_path.read_text(encoding="utf-8"))
        copied_meta.update(feature="forged-v0", change_id="forged-v0")
        copied_meta_path.write_text(json.dumps(copied_meta), encoding="utf-8")
        forged_registry = copy.deepcopy(registry_source)
        forged_registry["packages"].append(
            {
                "platform": "iOS",
                "feature": "forged-v0",
                "change_id": "forged-v0",
                "package_path": "iOS/specs/forged-v0/changes/forged-v0",
                "hashes": legacy_package_hashes(copied_package, copied_meta),
            }
        )
        registry_path = fixture_root / LEGACY_REGISTRY_PATH
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(json.dumps(forged_registry), encoding="utf-8")
        forged_findings = legacy_registry_findings(fixture_root)
        assert any(
            "code-pinned canonical trust anchor" in item["detail"]
            for item in forged_findings
        ), forged_findings

    for source_path, source_adapter in ((ios_path, ios_adapter), (path, adapter)):
        missing_contract_version = copy.deepcopy(source_adapter)
        missing_contract_version["modularity"].pop("contract_version")
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, missing_contract_version)
        )
        application_unit = copy.deepcopy(source_adapter)
        application_unit["modularity"]["physical_units"] = ["application target"]
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, application_unit)
        )
        missing_legacy_checks = copy.deepcopy(source_adapter)
        missing_legacy_checks["modularity"]["legacy_task_checks"] = []
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, missing_legacy_checks)
        )
        missing_phase_rule = copy.deepcopy(source_adapter)
        missing_phase_rule["phase_rule_profiles"]["propose"].remove(COMMON_MODULARITY_RULE)
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, missing_phase_rule)
        )
        missing_language_rule = copy.deepcopy(source_adapter)
        missing_language_rule["phase_rule_profiles"]["plan"].remove(ARTIFACT_LANGUAGE_RULE)
        assert any(
            ARTIFACT_LANGUAGE_RULE in item["detail"]
            for item in modularity_profile_findings(root, source_path, missing_language_rule)
        )
        missing_platform_rule = copy.deepcopy(source_adapter)
        platform_rule = missing_platform_rule["modularity"]["platform_rule"]
        missing_platform_rule["phase_rule_profiles"]["verify"].remove(platform_rule)
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, missing_platform_rule)
        )
        missing_scope = copy.deepcopy(source_adapter)
        missing_scope["modularity"]["isolation_scope"] = "missing-scope"
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, missing_scope)
        )
        missing_scope_check = copy.deepcopy(source_adapter)
        isolation_scope = missing_scope_check["modularity"]["isolation_scope"]
        missing_scope_check["scope_task_checks"][isolation_scope].remove("public contract")
        assert any(
            item["check"] == "cross-platform-modularity"
            for item in modularity_profile_findings(root, source_path, missing_scope_check)
        )

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

    missing_verify_capability = copy.deepcopy(adapter)
    missing_verify_capability["lifecycle_capabilities"] = ["propose", "plan", "implement"]
    assert validate_capabilities(missing_verify_capability) != [
        "propose", "plan", "implement", "verify", "archive-implementation",
    ]
    reordered_capability = copy.deepcopy(adapter)
    reordered_capability["lifecycle_capabilities"] = [
        "propose", "plan", "verify", "implement", "archive-implementation",
    ]
    try:
        validate_capabilities(reordered_capability)
    except RuleProfileError:
        pass
    else:
        raise AssertionError("reordered Android capabilities accepted")

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

    with tempfile.TemporaryDirectory() as tmp:
        fixture_root = Path(tmp).resolve()
        for raw in ANDROID_TERMINAL_CONTRACTS:
            target = fixture_root / raw
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text((root / raw).read_text(encoding="utf-8"), encoding="utf-8")
        assert android_terminal_addendum_findings(fixture_root) == []
        verify = fixture_root / "Android/workflow/phases/verify.md"
        verify.write_text(verify.read_text(encoding="utf-8") + "\nRun ./gradlew build in Xcode.\n", encoding="utf-8")
        mutated = android_terminal_addendum_findings(fixture_root)
        assert any(item["check"] == "android-fixed-assumption" for item in mutated)
        assert any(item["check"] == "android-platform-leakage" for item in mutated)

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
    assert check_reconciliation_flow(root) == []
    assert check_product_spec_review(root) == []
    assert check_platform_native_ux(root) == []
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp).resolve()
        for raw in PLATFORM_UX_REQUIRED:
            target = fixture / raw; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / raw).read_bytes())
        assert check_platform_native_ux(fixture) == []
        adapter_path = fixture / "Android/workflow/platform-contract.json"
        mutated = json.loads(adapter_path.read_text(encoding="utf-8"))
        mutated["platform_ux"]["design_language"] = "Assumed Expressive"
        adapter_path.write_text(json.dumps(mutated), encoding="utf-8")
        assert any(item["check"] == "platform-native-ux-adapter" for item in check_platform_native_ux(fixture))
        ios_role = fixture / "iOS/workflow/roles/ios-ux-designer.md"
        ios_role.write_text(
            ios_role.read_text(encoding="utf-8").replace(
                "../../../workflow/rules/visual-language.md", "missing-common-rule.md"
            ), encoding="utf-8",
        )
        assert any(item["check"] == "platform-native-ux-contract" for item in check_platform_native_ux(fixture))
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp).resolve()
        for raw in PRODUCT_REVIEW_REQUIRED:
            target = fixture / raw
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / raw).read_bytes())
        assert check_product_spec_review(fixture) == []
        role = fixture / "workflow/roles/product-spec-reviewer.md"
        role.write_text(
            role.read_text(encoding="utf-8").replace(
                "One invocation must not cover multiple lenses.",
                "One invocation may cover every lens.",
            ),
            encoding="utf-8",
        )
        mutated_product_review = check_product_spec_review(fixture)
        assert any(item["check"] == "product-spec-review-contract" for item in mutated_product_review)
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp).resolve()
        for raw in RECONCILIATION_REQUIRED:
            target = fixture / raw
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((root / raw).read_bytes())
        assert check_reconciliation_flow(fixture) == []
        (fixture / "workflow/rules/implementation-reconciliation.md").unlink()
        missing_reconciliation = check_reconciliation_flow(fixture)
        assert any(item["check"] == "implementation-reconciliation-files" for item in missing_reconciliation)
        target = fixture / "workflow/rules/implementation-reconciliation.md"
        target.write_bytes((root / "workflow/rules/implementation-reconciliation.md").read_bytes())
        hook = fixture / "workflow/hooks/hook-runner.py"
        hook.write_text(hook.read_text(encoding="utf-8") + "\nsubprocess.run(['reconcile-implementation.py'])\n", encoding="utf-8")
        unsafe_reconciliation = check_reconciliation_flow(fixture)
        assert any(item["check"] == "implementation-reconciliation-read-only-gate" for item in unsafe_reconciliation)
        binding = fixture / ".codex/agents/implementation-writer.toml"
        binding.write_text(
            binding.read_text(encoding="utf-8").replace("platform-reconciliation", "removed-mode"),
            encoding="utf-8",
        )
        broken_binding = check_reconciliation_flow(fixture)
        assert any(item["check"] == "implementation-reconciliation-role-binding" for item in broken_binding)
    unknown_scan = {
        "status": "UNKNOWN", "critical": 0, "coverage_complete": False,
        "coverage_issues": [{
            "category": "read-error", "path": "workflow/phases/example.md",
            "message": "Declared text surface cannot be read.",
        }],
        "findings": [],
    }
    unknown_findings = security_audit_payload_findings(
        "workflow/scripts/harness-security-audit.py", unknown_scan, 3,
    )
    assert any(item["check"] == "harness-security-coverage" for item in unknown_findings)
    assert security_audit_payload_findings(
        "workflow/scripts/harness-security-audit.py",
        {"status": "PASS", "critical": 0, "coverage_complete": True, "coverage_issues": [], "findings": []},
        0,
    ) == []
    for start in (root, root / "iOS", root / "Android"):
        result = subprocess.run(
            ["python3", str(root / "workflow/hooks/hook-runner.py"), "--runtime", "opencode", "--event", "pre-tool", "--root", str(root)],
            cwd=start, input=json.dumps({"tool": "write", "args": {"filePath": "workflow/README.md"}}),
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, f"OpenCode worktree-root payload failed from {start}: {result.stdout} {result.stderr}"
    for script in (
        "workflow/scripts/pre-commit-check.py",
        "workflow/scripts/git_change_paths.py",
        "workflow/scripts/platform_path_ownership.py",
        "workflow/hooks/hook-runner.py",
        "workflow/scripts/configure-git-hooks.sh",
        "workflow/scripts/validate-deep-code-review.py",
        "workflow/scripts/read-deep-code-review-report.py",
        "workflow/scripts/harness-security-audit.py",
        "workflow/scripts/deep-code-review-readonly-guard.py",
        "workflow/scripts/reconcile-implementation.py",
        "workflow/scripts/validate-product-spec.py",
    ):
        command = ["bash", script, "--self-test"] if script.endswith(".sh") else ["python3", script, "--self-test"]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        assert result.returncode == 0, f"{script} self-test failed: {result.stdout} {result.stderr}"
    print("harness-lint self-test: PASS (profiles + hooks + deep review security mutations)")
    return 0


PRODUCT_REVIEW_REQUIRED = (
    "workflow/rules/product-spec-review.md",
    "workflow/roles/product-spec-reviewer.md",
    "workflow/templates/product-review-verdict.json",
    "workflow/templates/product-spec.md",
    "workflow/phases/elaborate.md",
    ".agents/skills/elaborate/SKILL.md",
    "workflow/scripts/validate-product-spec.py",
    "workflow/scripts/validate-platform-change.py",
    "workflow/scripts/archive-change.py",
    ".codex/agents/product-spec-reviewer.toml",
    ".claude/agents/product-spec-reviewer.md",
    ".cursor/agents/product-spec-reviewer.md",
    ".opencode/agents/product-spec-reviewer.md",
)


def check_product_spec_review(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for raw in PRODUCT_REVIEW_REQUIRED:
        if not (root / raw).is_file():
            findings.append(finding(
                "critical", "product-spec-review-files", raw,
                "required independent product review artifact is missing",
            ))
    if findings:
        return findings
    required_tokens = {
        "workflow/rules/product-spec-review.md": (
            "product", "ux-accessibility", "design-system",
            "data-analytics-privacy", "security", "cross-client-parity",
            "separate fresh", "independent_context: false", "UNKNOWN",
            "review-verdicts.json", "only the exact Status",
            "provenance attestation", "not cryptographic proof", "`GAPS`",
            "exactly one", "unique REQ/AC",
        ),
        "workflow/roles/product-spec-reviewer.md": (
            "One invocation must not cover multiple lenses.", "Never edit/fix",
            "iOS", "Android", "semantic `GAP`", "threats", "localization",
            "including PASS", "runtime-issued", "not cryptographic proof",
        ),
        "workflow/phases/elaborate.md": (
            "ровно шесть", "отдельном fresh context", "aggregate --write",
            "validate-product-spec.py check", "parent review session",
            "durable non-green receipt",
        ),
        "workflow/scripts/validate-product-spec.py": (
            "STATUS_LINE_RE", "review-verdicts.json", "snapshot_product",
            "validate_verdict_data", "aggregate_data", "check_product",
            "product package root symlink", "--self-test", "parent_context_id",
            "provenance_ref", "exact_metadata", "duplicate REQ IDs", '"GAPS"',
        ),
        "workflow/scripts/validate-platform-change.py": ("validate_product_ready",),
        "workflow/scripts/archive-change.py": ("product review gate",),
        "workflow/templates/product-spec.md": (
            "Product review receipt", "UX readiness",
        ),
        "workflow/templates/product-review-verdict.json": (
            '"runtime"', '"parent_context_id"', '"provenance_ref"',
        ),
    }
    for raw, tokens in required_tokens.items():
        text = (root / raw).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(finding(
                    "critical", "product-spec-review-contract", raw,
                    f"missing invariant: {token}",
                ))
    for raw in (
        ".codex/agents/product-spec-reviewer.toml",
        ".claude/agents/product-spec-reviewer.md",
        ".cursor/agents/product-spec-reviewer.md",
        ".opencode/agents/product-spec-reviewer.md",
    ):
        text = (root / raw).read_text(encoding="utf-8").casefold()
        for token in (
            "read-only", "fresh", "one", "never", "receipt", "platform",
            "parent", "invocation evidence", "not cryptographic proof",
        ):
            if token not in text:
                findings.append(finding(
                    "critical", "product-spec-review-role-binding", raw,
                    f"runtime binding misses isolation/read-only token: {token}",
                ))
    if (root / ".agents/skills/product-spec-review/SKILL.md").exists():
        findings.append(finding(
            "critical", "product-spec-review-no-skill",
            ".agents/skills/product-spec-review/SKILL.md",
            "independent product review is an internal Elaborate gate, not a user-facing skill",
        ))
    return findings


PLATFORM_UX_REQUIRED = (
    "workflow/rules/visual-language.md", "workflow/templates/platform-ux.md",
    "iOS/workflow/rules/ui-design-system.md", "Android/workflow/rules/ui-design-system.md",
    "iOS/workflow/roles/ios-ux-designer.md", "Android/workflow/roles/android-ux-designer.md",
    "iOS/workflow/platform-contract.json", "Android/workflow/platform-contract.json",
    "workflow/scripts/validate-platform-change.py",
    ".codex/agents/ios-ux-designer.toml", ".claude/agents/ios-ux-designer.md",
    ".cursor/agents/ios-ux-designer.md", ".opencode/agents/ios-ux-designer.md",
    ".codex/agents/android-ux-designer.toml", ".claude/agents/android-ux-designer.md",
    ".cursor/agents/android-ux-designer.md", ".opencode/agents/android-ux-designer.md",
)


def check_platform_native_ux(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for raw in PLATFORM_UX_REQUIRED:
        if not (root / raw).is_file():
            findings.append(finding("critical", "platform-native-ux-files", raw, "required platform UX artifact is missing"))
    if findings:
        return findings
    token_map = {
        "workflow/rules/visual-language.md": ("calm", "soft-blue", "semantic roles", "quiet neutral", "high/increased-contrast", "platform implementations"),
        "workflow/templates/platform-ux.md": ("UX status", "Native design language adapter", "Color direction", "soft blue", "Fallback and availability", "Open gaps"),
        "iOS/workflow/rules/ui-design-system.md": ("Liquid Glass", "functional", "content background", "Reduce Transparency", "older-OS/SDK fallback"),
        "Android/workflow/rules/ui-design-system.md": ("Material 3", "M3 Expressive", "Dynamic color", "Android 12+", "soft-blue fallback"),
        "iOS/workflow/roles/ios-ux-designer.md": ("read completely", "../../../workflow/rules/visual-language.md", "../rules/ui-design-system.md", "Write only `platform-ux.md`"),
        "Android/workflow/roles/android-ux-designer.md": ("read completely", "../../../workflow/rules/visual-language.md", "../rules/ui-design-system.md", "Write only `platform-ux.md`"),
        "workflow/scripts/validate-platform-change.py": ("PLATFORM_UX_KEYS", "PLATFORM_UX_UNRESOLVED_RE", "platform_ux_exact_none", "validate_platform_ux", "platform-ux.md", "task_checks", "semantic_projection"),
    }
    for raw, tokens in token_map.items():
        text = (root / raw).read_text(encoding="utf-8")
        for token in tokens:
            if token.casefold() not in text.casefold():
                findings.append(finding("critical", "platform-native-ux-contract", raw, f"missing invariant: {token}"))
    common = (root / "workflow/rules/visual-language.md").read_text(encoding="utf-8")
    if "Liquid Glass" in common or "Material 3" in common:
        findings.append(finding("critical", "platform-native-ux-layering", "workflow/rules/visual-language.md", "shared rule must not own platform API language"))
    for platform, language, role in (("iOS", "Liquid Glass", "ios-ux-designer"), ("Android", "Material 3", "android-ux-designer")):
        raw = f"{platform}/workflow/platform-contract.json"
        try:
            adapter = json.loads((root / raw).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            findings.append(finding("critical", "platform-native-ux-adapter", raw, "adapter JSON is invalid")); continue
        config = adapter.get("platform_ux")
        if not isinstance(config, dict) or set(config) != {"role", "artifact", "design_language", "required_terms", "task_checks"}:
            findings.append(finding("critical", "platform-native-ux-adapter", raw, "platform_ux exact schema mismatch")); continue
        if config.get("role") != role or config.get("artifact") != "platform-ux.md" or config.get("design_language") != language:
            findings.append(finding("critical", "platform-native-ux-adapter", raw, "platform_ux identity/language mismatch"))
    return findings


RECONCILIATION_REQUIRED = (
    ".agents/skills/reconcile-implementation/SKILL.md",
    ".agents/skills/reconcile-implementation/agents/openai.yaml",
    ".claude/commands/reconcile-implementation.md",
    ".opencode/commands/reconcile-implementation.md",
    "workflow/phases/reconcile-implementation.md",
    "workflow/rules/implementation-reconciliation.md",
    "workflow/scripts/reconcile-implementation.py",
    "workflow/roles/implementation-discovery.md",
    "workflow/roles/specification-writer.md",
    "workflow/roles/architecture-designer.md",
    "workflow/roles/implementation-planner.md",
    "workflow/roles/implementation-writer.md",
    "workflow/phases/pre-commit-check.md",
    "workflow/rules/pre-commit-integrity.md",
    "workflow/rules/hook-contract.md",
    "workflow/scripts/pre-commit-check.py",
    "workflow/scripts/git_change_paths.py",
    "workflow/scripts/platform_path_ownership.py",
    "workflow/hooks/hook-runner.py",
    "iOS/workflow/phases/reconcile-implementation.md",
    "Android/workflow/phases/reconcile-implementation.md",
    ".codex/agents/implementation-writer.toml",
    ".claude/agents/implementation-writer.md",
    ".cursor/agents/implementation-writer.md",
    ".opencode/agents/implementation-writer.md",
)


def check_reconciliation_flow(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for raw in RECONCILIATION_REQUIRED:
        if not (root / raw).is_file():
            findings.append(finding(
                "critical", "implementation-reconciliation-files", raw,
                "required reconciliation artifact is missing",
            ))
    if findings:
        return findings

    required_tokens = {
        "workflow/rules/implementation-reconciliation.md": (
            "explicit intended path set", "task-drift",
            "platform-implementation-drift", "ROUTE_REQUIRED", "mode `0600`",
            "terminal lifecycle step", "infer authorization",
        ),
        "workflow/phases/reconcile-implementation.md": (
            "implementation-discovery", "specification-writer",
            "architecture-designer", "implementation-planner",
            "implementation-writer", "inspect", "start", "check <token>",
        ),
        "workflow/scripts/reconcile-implementation.py": (
            "repository_snapshot", "index_projection", "lane_projection", "task_coverage",
            "affected_task_closure", "verification_status", "validate_package",
            "os.chmod", "--self-test",
        ),
        ".agents/skills/reconcile-implementation/agents/openai.yaml": (
            "allow_implicit_invocation: false",
        ),
        "workflow/phases/pre-commit-check.md": (
            "$reconcile-implementation", "не запускает reconciliation",
            "exact intended", "--hook", "one-shot receipt",
        ),
        "workflow/rules/pre-commit-integrity.md": (
            "non-consuming preview", "one-shot", "wrong-mode", "replay", "-Infinity",
        ),
        "workflow/scripts/pre-commit-check.py": (
            "issue_receipt", "hook_evaluate", "RECEIPT_TTL_SECONDS", "0o700", "0o600",
            "parse_constant", "math.isfinite",
        ),
        "workflow/scripts/git_change_paths.py": (
            "normalize_for_intent", "identity_paths", "mutable_paths", "read_only_paths",
            "head_path_entry", "index_path_entries", "index_stage != \"0\"",
        ),
        "workflow/scripts/platform_path_ownership.py": (
            "validate_platform_writable_path", "first_symlink", "proposed-child symlinks",
        ),
        "workflow/rules/hook-contract.md": (
            "не запускает `reconcile-implementation`", "actionable hint",
        ),
    }
    for raw, tokens in required_tokens.items():
        text = (root / raw).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(finding(
                    "critical", "implementation-reconciliation-contract", raw,
                    f"missing invariant: {token}",
                ))

    metadata = (root / ".agents/skills/reconcile-implementation/agents/openai.yaml").read_text(encoding="utf-8")
    if "allow_implicit_invocation: false" not in metadata:
        findings.append(finding(
            "critical", "implementation-reconciliation-manual-only",
            ".agents/skills/reconcile-implementation/agents/openai.yaml",
            "implicit invocation must remain disabled",
        ))

    for raw in ("workflow/scripts/pre-commit-check.py", "workflow/hooks/hook-runner.py"):
        text = (root / raw).read_text(encoding="utf-8")
        if "reconcile-implementation.py" in text or re.search(
            r"subprocess\.(?:run|Popen)[^\n]*reconcile-implementation", text,
        ):
            findings.append(finding(
                "critical", "implementation-reconciliation-read-only-gate", raw,
                "gate/hook must not invoke reconciliation",
            ))
        if "reconcile-implementation" not in text:
            findings.append(finding(
                "critical", "implementation-reconciliation-hint", raw,
                "actionable reconciliation hint is missing",
            ))

    for raw in (
        ".codex/agents/implementation-writer.toml",
        ".claude/agents/implementation-writer.md",
        ".cursor/agents/implementation-writer.md",
        ".opencode/agents/implementation-writer.md",
    ):
        text = (root / raw).read_text(encoding="utf-8")
        for token in ("harness", "platform-implementation", "platform-reconciliation", "guard", "production"):
            if token not in text:
                findings.append(finding(
                    "critical", "implementation-reconciliation-role-binding", raw,
                    f"implementation-writer binding misses mode/boundary token: {token}",
                ))

    ios_text = (root / "iOS/workflow/phases/reconcile-implementation.md").read_text(encoding="utf-8")
    android_text = (root / "Android/workflow/phases/reconcile-implementation.md").read_text(encoding="utf-8")
    if re.search(r"\b(?:Kotlin|Compose|Gradle|coroutine)\b", ios_text, re.IGNORECASE):
        findings.append(finding("critical", "implementation-reconciliation-platform-isolation", "iOS/workflow/phases/reconcile-implementation.md", "iOS addendum leaks Android technology"))
    if re.search(r"\b(?:Swift|SwiftUI|UIKit|Xcode|Apple SDK)\b", android_text, re.IGNORECASE):
        findings.append(finding("critical", "implementation-reconciliation-platform-isolation", "Android/workflow/phases/reconcile-implementation.md", "Android addendum leaks iOS technology"))
    return findings


def check_deep_code_review(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = (
        ".agents/skills/deep-code-review/SKILL.md",
        ".agents/skills/deep-code-review/agents/openai.yaml",
        ".claude/commands/deep-code-review.md",
        ".opencode/commands/deep-code-review.md",
        "workflow/phases/deep-code-review.md",
        "workflow/rules/code-review.md",
        "workflow/rules/bug-investigation.md",
        "workflow/rules/security-review.md",
        "workflow/roles/deep-code-reviewer.md",
        "workflow/roles/bug-investigator.md",
        "workflow/roles/security-reviewer.md",
        "workflow/scripts/validate-deep-code-review.py",
        "workflow/scripts/deep_code_review_report.py",
        "workflow/scripts/read-deep-code-review-report.py",
        "workflow/scripts/harness-security-audit.py",
        "workflow/scripts/deep-code-review-readonly-guard.py",
        "iOS/workflow/phases/deep-code-review.md",
        "Android/workflow/phases/deep-code-review.md",
    )
    for raw in required:
        if not (root / raw).is_file():
            findings.append(finding("critical", "deep-code-review-contract", raw, "required file is missing"))

    phase_path = root / "workflow/phases/deep-code-review.md"
    if phase_path.is_file():
        phase = phase_path.read_text(encoding="utf-8")
        required_tokens = (
            "writes_artifacts: []", "review <platform> <feature>",
            "feedback <platform> <feature>", "bug <platform> <feature>",
            "security [--json]", "Fresh-eyes independence: UNAVAILABLE",
            "accepted", "rejected", "duplicate", "needs-evidence",
            "No edits made", "verify android",
            "deep-code-review-readonly-guard.py start",
            "deep-code-review-readonly-guard.py check <token>",
            "read-deep-code-review-report.py <path>",
        )
        for token in required_tokens:
            if token not in phase:
                findings.append(finding("critical", "deep-code-review-contract", relative(phase_path, root), f"missing invariant: {token}"))

    skill_meta = root / ".agents/skills/deep-code-review/agents/openai.yaml"
    if skill_meta.is_file() and "allow_implicit_invocation: false" not in skill_meta.read_text(encoding="utf-8"):
        findings.append(finding("critical", "deep-code-review-manual-only", relative(skill_meta, root), "implicit invocation must be disabled"))

    validator_path = root / "workflow/scripts/validate-deep-code-review.py"
    if validator_path.is_file():
        validator = validator_path.read_text(encoding="utf-8")
        for token in ("platform_root", "pre_commit", "secret_globs", "report_sha256", "report_size"):
            if token not in validator:
                findings.append(finding("critical", "deep-code-review-path-contract", relative(validator_path, root), f"validator misses {token}"))
    guard_path = root / "workflow/scripts/deep-code-review-readonly-guard.py"
    if guard_path.is_file():
        guard = guard_path.read_text(encoding="utf-8")
        for token in ("GIT_OPTIONAL_LOCKS", "--cached", "--others", "MAX_FILES", "MAX_TOTAL_BYTES", "MAX_STATE_BYTES", "O_NOFOLLOW", "0o600"):
            if token not in guard:
                findings.append(finding("critical", "deep-code-review-readonly-guard", relative(guard_path, root), f"guard misses {token}"))
    report_helper = root / "workflow/scripts/deep_code_review_report.py"
    report_reader = root / "workflow/scripts/read-deep-code-review-report.py"
    if report_helper.is_file():
        helper = report_helper.read_text(encoding="utf-8")
        for token in ("O_NOFOLLOW", "MAX_REPORT_BYTES", "os.fstat", "sha256"):
            if token not in helper:
                findings.append(finding("critical", "deep-code-review-report-reader", relative(report_helper, root), f"report helper misses {token}"))
    if report_reader.is_file():
        reader = report_reader.read_text(encoding="utf-8")
        for token in ("expected_sha256", "expected_size", "read_report_snapshot"):
            if token not in reader:
                findings.append(finding("critical", "deep-code-review-report-reader", relative(report_reader, root), f"report reader misses {token}"))
    scanner_path = root / "workflow/scripts/harness-security-audit.py"
    if scanner_path.is_file():
        scanner = scanner_path.read_text(encoding="utf-8")
        for token in ("O_NOFOLLOW", "candidate-set-race", "os.fstat", "coverage_issues"):
            if token not in scanner:
                findings.append(finding("critical", "harness-security-coverage", relative(scanner_path, root), f"scanner misses {token}"))

    roles = ("deep-code-reviewer", "bug-investigator", "security-reviewer")
    binding_requirements = {
        "codex": (".codex/agents/{role}.toml", "never write"),
        "claude": (".claude/agents/{role}.md", "permissionMode: plan"),
        "cursor": (".cursor/agents/{role}.md", "readonly: true"),
        "opencode": (".opencode/agents/{role}.md", "edit: deny"),
    }
    for role in roles:
        canonical = root / f"workflow/roles/{role}.md"
        if canonical.is_file() and "read-only" not in canonical.read_text(encoding="utf-8").casefold():
            findings.append(finding("critical", "deep-code-review-read-only", relative(canonical, root), "canonical role must be explicitly read-only"))
        for runtime, (template, marker) in binding_requirements.items():
            raw = template.format(role=role)
            path = root / raw
            if not path.is_file():
                findings.append(finding("critical", "deep-code-review-role-binding", raw, f"{runtime} binding is missing"))
            elif marker not in path.read_text(encoding="utf-8"):
                findings.append(finding("critical", "deep-code-review-read-only", raw, f"missing read-only marker: {marker}"))

    for legacy in ("deep-review", "receiving-code-review", "bug-resolver", "security-audit"):
        path = root / ".agents/skills" / legacy
        if path.exists():
            findings.append(finding("critical", "deep-code-review-duplicate", relative(path, root), "legacy duplicate skill is forbidden"))

    ios = root / "iOS/workflow/phases/deep-code-review.md"
    android = root / "Android/workflow/phases/deep-code-review.md"
    if ios.is_file():
        text = ios.read_text(encoding="utf-8")
        if "verify ios" not in text or re.search(r"\b(?:Android|Gradle|Kotlin|Compose)\b", text):
            findings.append(finding("critical", "deep-code-review-platform-isolation", relative(ios, root), "iOS addendum has wrong terminal route or Android leakage"))
    if android.is_file():
        text = android.read_text(encoding="utf-8")
        if "verify android" not in text or "terminal Verify unavailable" in text or re.search(r"\b(?:Swift|SwiftUI|UIKit|Xcode)\b", text):
            findings.append(finding("critical", "deep-code-review-platform-isolation", relative(android, root), "Android addendum has wrong terminal route or iOS leakage"))
    return findings


def check_security_audit(root: Path) -> list[dict[str, str]]:
    script = root / "workflow/scripts/harness-security-audit.py"
    if not script.is_file():
        return [finding("critical", "harness-security-audit", relative(script, root), "scanner is unavailable")]
    completed = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--json"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return [finding("critical", "harness-security-audit", relative(script, root), "scanner returned invalid output")]
    return security_audit_payload_findings(relative(script, root), payload, completed.returncode)


def security_audit_payload_findings(
    script: Path | str, payload: object, returncode: int,
) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return [finding("critical", "harness-security-audit", script, "scanner payload must be an object")]
    findings: list[dict[str, str]] = []
    scanner_findings = payload.get("findings", [])
    if not isinstance(scanner_findings, list):
        findings.append(finding("critical", "harness-security-audit", script, "scanner findings schema is invalid"))
        scanner_findings = []
    for item in scanner_findings:
        if not isinstance(item, dict):
            findings.append(finding("critical", "harness-security-audit", script, "scanner finding schema is invalid"))
            continue
        severity = "critical" if item.get("severity") == "critical" else "warning"
        label = f"{item.get('path', '?')}:{item.get('line', '?')}"
        findings.append(finding(severity, "harness-security-audit", label, str(item.get("message", "security finding"))))
    status = payload.get("status")
    expected_exit = {"PASS": 0, "FAIL": 2, "UNKNOWN": 3}
    if status not in expected_exit or returncode != expected_exit.get(status):
        findings.append(finding("critical", "harness-security-audit", script, "scanner status/exit contract is invalid"))
    coverage = payload.get("coverage_issues", [])
    if not isinstance(coverage, list):
        findings.append(finding("critical", "harness-security-coverage", script, "coverage_issues schema is invalid"))
        coverage = []
    for item in coverage:
        if not isinstance(item, dict):
            findings.append(finding("critical", "harness-security-coverage", script, "coverage issue schema is invalid"))
            continue
        label = str(item.get("path", script))
        detail = str(item.get("message", "harness security coverage is incomplete"))
        findings.append(finding("critical", "harness-security-coverage", label, detail))
    if status == "UNKNOWN" and not coverage:
        findings.append(finding("critical", "harness-security-coverage", script, "scanner returned UNKNOWN without a coverage issue"))
    if payload.get("coverage_complete") is not (not coverage):
        findings.append(finding("critical", "harness-security-coverage", script, "coverage_complete contradicts coverage issues"))
    return findings


def check_engineering_rule_profiles(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required = (
        "workflow/rules/coding-standards.md", "workflow/rules/code-comments.md",
        "workflow/rules/tdd-first.md", "workflow/rules/test-execution.md",
        "workflow/rules/verification-matrix.md", "workflow/rules/git-conventions.md",
        "workflow/rules/branching.md", "workflow/rules/developer-experience.md",
        "workflow/rules/system-design/modularity.md",
        "workflow/rules/artifact-language.md",
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
        "package": {"package consumer", "consumer integration", "package build", "public contract", "dependency graph", "app-shell wiring"},
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
    findings.extend(modularity_profile_findings(root, adapter_path, adapter))

    template = root / "workflow/templates/platform-meta.json"
    if template.is_file():
        text = template.read_text(encoding="utf-8")
        for token in ('"engineering_scopes"', '"applicable_rule_files"', '"rule_selection_snapshot"', '"modularity_contract_version": 1'):
            if token not in text:
                findings.append(finding("critical", "engineering-meta", relative(template, root), f"missing field: {token}"))
    selection_template = root / "workflow/templates/platform-rule-selection.json"
    if not selection_template.is_file():
        findings.append(finding("critical", "engineering-meta", "workflow/templates/platform-rule-selection.json", "planned selection snapshot template is missing"))
    else:
        selection_text = selection_template.read_text(encoding="utf-8")
        for token in ('"schema_version": 2', '"modularity_contract_version": 1'):
            if token not in selection_text:
                findings.append(finding("critical", "engineering-meta", relative(selection_template, root), f"missing field: {token}"))
    modularity_wiring = {
        "workflow/templates/platform-design.md": (
            "Modularity decision", "Capability triggers", "Physical boundaries",
            "Public contracts and dependency direction", "App-shell responsibilities",
            "App-shell capability ownership", "Repository evidence", "Migration boundary and trigger",
            "Over-modularization check", "Boundary guard verdict",
        ),
        "workflow/templates/platform-plan-task.md": ("Boundary owner",),
        "workflow/templates/platform-verification.md": (
            "Modularity verification", "Dependency graph", "Public API and visibility",
            "Module-level tests", "Consumer integration and build", "App-shell allowlist",
        ),
        "workflow/roles/architecture-designer.md": ("Modularity decision", "PASS", "BLOCK"),
        "workflow/roles/implementation-planner.md": ("Boundary owner", "consumer integration", "app-shell"),
        "workflow/roles/implementation-writer.md": ("application shell", "feature/domain/data/network"),
        "workflow/roles/verifier.md": ("dependency graph", "public API/visibility", "UNKNOWN"),
    }
    for raw, tokens in modularity_wiring.items():
        path = root / raw
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        for token in tokens:
            if token not in text:
                findings.append(finding("critical", "cross-platform-modularity", raw, f"missing wiring token: {token}"))
    language_wiring = {
        "workflow/templates/platform-proposal.md": ("по-русски",),
        "workflow/templates/platform-implementation-spec.md": ("по-русски",),
        "workflow/templates/platform-design.md": ("по-русски",),
        "workflow/templates/platform-ux.md": ("по-русски",),
        "workflow/templates/platform-verification.md": ("по-русски",),
        "workflow/templates/platform-plan-readme.md": ("по-русски",),
        "workflow/templates/platform-plan-task.md": ("по-русски",),
        "workflow/roles/specification-writer.md": ("artifact-language", "по-русски"),
        "workflow/roles/architecture-designer.md": ("artifact-language", "по-русски"),
        "workflow/roles/implementation-planner.md": ("artifact-language", "по-русски"),
        "workflow/roles/implementation-writer.md": (
            "artifact-language", "evidence/task-NNN.md", "reconciliation reports",
        ),
        "workflow/roles/verifier.md": ("artifact-language", "по-русски"),
        "iOS/workflow/roles/ios-ux-designer.md": ("artifact-language", "по-русски"),
        "Android/workflow/roles/android-ux-designer.md": ("artifact-language", "по-русски"),
        "workflow/scripts/validate-platform-change.py": (
            "validate_authored_markdown_language", "ARTIFACT_LANGUAGE_RULE",
            "import artifact_language",
            "TASK_AUTHORED_REPORT_RE", "RECONCILIATION_AUTHORED_REPORT_RE",
            "typed_authored_report_paths", "evidence.iterdir()",
        ),
        "workflow/scripts/artifact_language.py": (
            "(+{len(failing) - 3} more)", "authored_relative = path.relative_to(package)",
            "current.is_symlink()", "resolved_path, resolved_package",
            'encoding="utf-8", errors="strict"',
            "_english_sentence", "validate_authored_json_string",
        ),
        "workflow/phases/implement.md": ("artifact-language", "evidence/task-NNN.md"),
        "workflow/phases/reconcile-implementation.md": (
            "artifact-language", "evidence/reconciliation-<timestamp>-task-NNN",
        ),
    }
    for raw, tokens in language_wiring.items():
        path = root / raw
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        for token in tokens:
            if token not in text:
                findings.append(finding(
                    "critical", "russian-platform-artifacts", raw,
                    f"missing wiring token: {token}",
                ))
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
        "Swin" + "ject", "Mae" + "stro",
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
            findings.extend(modularity_profile_findings(root, android_adapter_path, android_adapter))
    findings.extend(android_terminal_addendum_findings(root))
    findings.extend(android_assumption_findings(root))
    for runtime in (".claude", ".opencode"):
        for command in ("propose", "plan", "implement"):
            path = root / runtime / "commands" / f"{command}.md"
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            if "Android" not in text or "поддержан iOS" in text:
                findings.append(finding("critical", "android-runtime-capability", relative(path, root), f"{command} command must describe Android capability support"))
        verify_path = root / runtime / "commands/verify.md"
        verify_text = verify_path.read_text(encoding="utf-8") if verify_path.is_file() else ""
        if (
            "Android" not in verify_text
            or re.search(r"\b(?:blocked|unsupported|NOT IMPLEMENTED)\b", verify_text, re.IGNORECASE)
        ):
            findings.append(finding("critical", "android-runtime-capability", relative(verify_path, root), "verify command must describe Android support without a blocker"))
        archive_path = root / runtime / "commands/archive.md"
        archive_text = archive_path.read_text(encoding="utf-8") if archive_path.is_file() else ""
        if re.search(r"Android.*(?:blocked|unsupported|NOT IMPLEMENTED)", archive_text, re.IGNORECASE):
            findings.append(finding("critical", "android-runtime-capability", relative(archive_path, root), "archive command contains a stale Android blocker"))
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
        result = self_test_android_lint(root)
        module, error = load_docs_checker(root)
        if error:
            raise AssertionError(error)
        module.self_test(root)
        return result
    markdown_files = iter_files(root, (".md",))
    findings: list[dict[str, str]] = []
    findings.extend(check_repository_docs(root))
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
    findings.extend(check_reconciliation_flow(root))
    findings.extend(check_product_spec_review(root))
    findings.extend(check_platform_native_ux(root))
    findings.extend(check_deep_code_review(root))
    findings.extend(check_security_audit(root))
    findings.extend(check_engineering_rule_profiles(root))
    findings.extend(legacy_registry_findings(root))
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
