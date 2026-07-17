#!/usr/bin/env python3
"""Render and verify deterministic root documentation projections."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import unquote


DOC_BLOCKS = {
    "README.md": ("README_CAPABILITIES",),
    "workflow.md": ("WORKFLOW_SKILLS",),
    "deep-info.md": ("DEEP_WIRING", "DEEP_INVENTORY", "DEEP_RUNTIME_PARITY"),
}
INVENTORY_DIRS = (
    ".agents",
    ".codex",
    ".claude",
    ".cursor",
    ".opencode",
    "workflow",
    "process",
    "iOS/workflow",
    "Android/workflow",
)
INVENTORY_ROOT_FILES = (
    ".gitignore",
    ".githooks/pre-commit",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "specs/product/README.md",
    "iOS/specs/README.md",
    "Android/specs/README.md",
    "deep-info.md",
    "iOS/AGENTS.md",
    "Android/AGENTS.md",
    "opencode.json",
    "third_party/NOTICE.md",
    "workflow.md",
)
EXCLUDED_DIRS = {
    ".git", ".build", ".gradle", ".idea", ".kotlin", ".swiftpm",
    "DerivedData", "__pycache__", "build", "node_modules", "specs", "worktrees",
}
EXCLUDED_FILES = {".ds_store", "thumbs.db", "desktop.ini"}
EXCLUDED_INVENTORY_PATHS = {
    ".opencode/.gitignore",
    ".opencode/bun.lock",
    ".opencode/package-lock.json",
    ".opencode/package.json",
}
EXCLUDED_INVENTORY_PREFIXES = (
    "workflow/archive-requests/",
)
REQUIRED_DOCUMENTATION_SURFACES = (
    "workflow/rules/repository-documentation.md",
    "workflow/phases/harness-change.md",
    "workflow/phases/harness-review.md",
    "workflow/roles/harness-auditor.md",
    "workflow/templates/harness-change.md",
    "workflow/test-evidence/root-documentation.md",
)
CAPABILITY_PHASE = {
    "propose": "propose",
    "plan": "plan",
    "implement": "implement",
    "verify": "verify",
    "archive-implementation": "archive",
}
RUNTIME_SPECS = {
    "Codex": {
        "skills": ".agents/skills/",
        "commands": None,
        "roles": ".codex/agents",
        "binding": ".codex/hooks.json",
    },
    "Claude Code": {
        "skills": ".agents/skills/",
        "commands": ".claude/commands",
        "roles": ".claude/agents",
        "binding": ".claude/settings.json",
    },
    "Cursor": {
        "skills": ".agents/skills/",
        "commands": None,
        "roles": ".cursor/agents",
        "binding": ".cursor/hooks.json",
    },
    "OpenCode": {
        "skills": ".agents/skills/",
        "commands": ".opencode/commands",
        "roles": ".opencode/agents",
        "binding": ".opencode/plugins/harness-hooks.ts",
    },
}
MARKER_RE = re.compile(r"<!--\s*(BEGIN|END) GENERATED: ([A-Z0-9_]+)\s*-->")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


class DocsError(ValueError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise DocsError(f"{path}: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise DocsError(f"{path}: unterminated YAML frontmatter") from error
    data: dict[str, object] = {}
    current_list: str | None = None
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if raw.startswith("  - "):
            if current_list is None or not isinstance(data.get(current_list), list):
                raise DocsError(f"{path}: list item without a key: {raw}")
            data[current_list].append(raw[4:].strip())
            continue
        if raw.startswith((" ", "\t")):
            if ":" not in raw:
                raise DocsError(f"{path}: malformed nested frontmatter line: {raw}")
            continue
        if ":" not in raw:
            raise DocsError(f"{path}: malformed frontmatter line: {raw}")
        key, value = raw.split(":", 1)
        key = key.strip()
        if not key or key in data:
            raise DocsError(f"{path}: duplicate or empty frontmatter key: {key}")
        value = value.strip()
        if value:
            data[key] = value.strip('"\'')
            current_list = None
        else:
            data[key] = []
            current_list = key
    return data, "\n".join(lines[end + 1 :])


def load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DocsError(f"{path}: invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise DocsError(f"{path}: JSON root must be an object")
    return value


def load_skills(root: Path) -> dict[str, dict[str, object]]:
    skills_root = root / ".agents/skills"
    if not skills_root.is_dir():
        raise DocsError(".agents/skills: portable skill root is missing")
    skills: dict[str, dict[str, object]] = {}
    for directory in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        skill_file = directory / "SKILL.md"
        metadata_file = directory / "agents/openai.yaml"
        if not skill_file.is_file() or not metadata_file.is_file():
            raise DocsError(f"{repo_path(directory, root)}: incomplete portable skill surface")
        metadata, _ = read_frontmatter(skill_file)
        if metadata.get("name") != directory.name or not metadata.get("description"):
            raise DocsError(f"{repo_path(skill_file, root)}: invalid name or description")
        phase = root / "workflow/phases" / f"{directory.name}.md"
        if not phase.is_file():
            raise DocsError(f"{repo_path(skill_file, root)}: canonical phase is missing")
        phase_metadata, _ = read_frontmatter(phase)
        if phase_metadata.get("phase") != directory.name:
            raise DocsError(f"{repo_path(phase, root)}: phase identity mismatch")
        skills[directory.name] = {
            "description": str(metadata["description"]),
            "phase": phase,
            "phase_metadata": phase_metadata,
        }
    return skills


def canonical_roles(root: Path) -> set[str]:
    result: set[str] = set()
    for directory in (
        root / "workflow/roles",
        root / "iOS/workflow/roles",
        root / "Android/workflow/roles",
    ):
        if not directory.is_dir():
            raise DocsError(f"{repo_path(directory, root)}: canonical role directory is missing")
        result.update(path.stem for path in directory.glob("*.md"))
    return result


def runtime_role_names(root: Path, directory: str) -> set[str]:
    path = root / directory
    if not path.is_dir():
        raise DocsError(f"{directory}: runtime role directory is missing")
    names: set[str] = set()
    for item in sorted(path.iterdir()):
        if item.suffix == ".toml":
            try:
                value = tomllib.loads(item.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as error:
                raise DocsError(f"{repo_path(item, root)}: invalid TOML: {error}") from error
            name = value.get("name")
        elif item.suffix == ".md":
            metadata, _ = read_frontmatter(item)
            name = metadata.get("name", item.stem)
        else:
            continue
        if name != item.stem or name in names:
            raise DocsError(f"{repo_path(item, root)}: invalid or duplicate role identity")
        names.add(str(name))
    return names


def load_platforms(root: Path) -> dict[str, dict[str, object]]:
    platforms: dict[str, dict[str, object]] = {}
    for platform_root in ("iOS", "Android"):
        path = root / platform_root / "workflow/platform-contract.json"
        adapter = load_json(path)
        required = {
            "platform_input", "platform_name", "platform_root", "package_root",
            "lifecycle_capabilities", "phase_rule_profiles", "rule_files",
        }
        missing = sorted(required - set(adapter))
        if missing:
            raise DocsError(f"{repo_path(path, root)}: missing keys: {', '.join(missing)}")
        if adapter.get("platform_root") != platform_root:
            raise DocsError(f"{repo_path(path, root)}: platform_root mismatch")
        capabilities = adapter.get("lifecycle_capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            raise DocsError(f"{repo_path(path, root)}: invalid lifecycle_capabilities")
        for capability in capabilities:
            phase_name = CAPABILITY_PHASE.get(str(capability))
            if phase_name is None:
                raise DocsError(f"{repo_path(path, root)}: unknown capability {capability}")
            addendum = root / platform_root / "workflow/phases" / f"{phase_name}.md"
            if not addendum.is_file():
                raise DocsError(f"{repo_path(path, root)}: missing addendum {phase_name}.md")
        for field in ("rule_files",):
            values = adapter.get(field)
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                raise DocsError(f"{repo_path(path, root)}: invalid {field}")
            for raw in values:
                if not (root / raw).is_file():
                    raise DocsError(f"{repo_path(path, root)}: missing referenced rule {raw}")
        profiles = adapter.get("phase_rule_profiles")
        if not isinstance(profiles, dict):
            raise DocsError(f"{repo_path(path, root)}: invalid phase_rule_profiles")
        for phase_name, values in profiles.items():
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                raise DocsError(f"{repo_path(path, root)}: invalid profile {phase_name}")
            for raw in values:
                if not (root / raw).is_file():
                    raise DocsError(f"{repo_path(path, root)}: missing profile rule {raw}")
        platforms[platform_root] = adapter
    return platforms


def validate_runtime_bindings(root: Path, skills: set[str]) -> None:
    expected_roles = canonical_roles(root)
    for runtime, spec in RUNTIME_SPECS.items():
        roles = runtime_role_names(root, str(spec["roles"]))
        if roles != expected_roles:
            missing = sorted(expected_roles - roles)
            extra = sorted(roles - expected_roles)
            raise DocsError(f"{runtime}: role parity mismatch; missing={missing}, extra={extra}")
        commands_dir = spec["commands"]
        if commands_dir:
            directory = root / str(commands_dir)
            if not directory.is_dir():
                raise DocsError(f"{commands_dir}: command directory is missing")
            commands = {path.stem for path in directory.glob("*.md")}
            if commands != skills:
                raise DocsError(f"{runtime}: command parity mismatch")
            for name in sorted(skills):
                path = directory / f"{name}.md"
                read_frontmatter(path)
                text = path.read_text(encoding="utf-8")
                direct = f".agents/skills/{name}/SKILL.md" in text
                native = runtime == "OpenCode" and "native skill tool" in text and f"`{name}`" in text
                if not direct and not native:
                    raise DocsError(f"{repo_path(path, root)}: portable skill binding is missing")
        binding = root / str(spec["binding"])
        if not binding.is_file():
            raise DocsError(f"{spec['binding']}: runtime binding is missing")
    for path in (
        root / ".codex/hooks.json",
        root / ".claude/settings.json",
        root / ".cursor/hooks.json",
        root / "opencode.json",
    ):
        load_json(path)
    for path in (root / ".githooks/pre-commit", root / ".opencode/plugins/harness-hooks.ts"):
        if not path.is_file():
            raise DocsError(f"{repo_path(path, root)}: required hook surface is missing")


def discover_source_roots(root: Path, platform: str) -> list[str]:
    base = root / platform
    if platform == "iOS":
        candidates = {
            path.parent.parent
            for path in base.rglob("project.pbxproj")
            if path.parent.suffix == ".xcodeproj" and not EXCLUDED_DIRS.intersection(path.parts)
        }
    else:
        candidates = {
            path.parent
            for path in base.rglob("build.gradle.kts")
            if (path.parent / "src").is_dir() and not EXCLUDED_DIRS.intersection(path.parts)
        }
        candidates.update(
            path.parent
            for path in base.rglob("build.gradle")
            if (path.parent / "src").is_dir() and not EXCLUDED_DIRS.intersection(path.parts)
        )
    result = sorted(repo_path(path, root) + "/" for path in candidates)
    if not result:
        raise DocsError(f"{platform}: native source/build root was not discovered")
    return result


def inventory_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for raw in INVENTORY_DIRS:
        directory = root / raw
        if not directory.is_dir():
            raise DocsError(f"{raw}: inventory root is missing")
        for base, dirs, names in os.walk(directory):
            dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
            for name in names:
                if name.casefold() in EXCLUDED_FILES:
                    continue
                path = Path(base) / name
                relative_path = repo_path(path, root)
                if relative_path in EXCLUDED_INVENTORY_PATHS or relative_path.startswith(EXCLUDED_INVENTORY_PREFIXES):
                    continue
                if path.is_file():
                    files.add(path)
    for raw in INVENTORY_ROOT_FILES:
        path = root / raw
        if path.is_file():
            files.add(path)
    return sorted(files, key=lambda path: repo_path(path, root))


def first_heading(path: Path) -> str | None:
    if path.suffix != ".md":
        return None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def file_purpose(path: Path, root: Path) -> str:
    heading = first_heading(path)
    if heading:
        return heading
    raw = repo_path(path, root)
    if path.suffix == ".py":
        match = re.search(r'^[ru]*["\']{3}(.+?)["\']{3}', path.read_text(encoding="utf-8", errors="ignore"), re.DOTALL | re.MULTILINE)
        if match:
            return " ".join(match.group(1).split())
        return "Исполняемый stdlib-инструмент харнеса"
    if raw.endswith("agents/openai.yaml"):
        return "Codex metadata portable skill"
    if raw.endswith("platform-contract.json"):
        return "Capability, profile и ownership contract платформы"
    if "/commands/" in raw:
        return "Thin runtime command к portable skill"
    if "/agents/" in raw or raw.startswith(".codex/agents/"):
        return "Runtime binding канонической роли"
    if "hooks" in raw or path.name == "pre-commit":
        return "Runtime или Git hook binding"
    if path.suffix == ".json":
        return "Runtime/configuration contract"
    if path.suffix == ".toml":
        return "Runtime role/configuration binding"
    if path.suffix in {".sh", ".ts"}:
        return "Исполняемый adapter харнеса"
    if path.name == ".gitignore":
        return "Исключения transient/build state"
    return "Структурный ресурс харнеса"


def category(path: Path, root: Path) -> str:
    raw = repo_path(path, root)
    if raw.startswith("workflow/phases/"): return "Common phases"
    if raw.startswith("workflow/rules/"): return "Common rules"
    if raw.startswith("workflow/roles/"): return "Common roles"
    if raw.startswith("workflow/scripts/"): return "Scripts"
    if raw.startswith("workflow/templates/"): return "Templates"
    if raw.startswith("workflow/hooks/"): return "Common hooks"
    if raw.startswith("workflow/test-evidence/"): return "Test evidence"
    if raw.startswith("process/"): return "Process map"
    if raw.startswith(".agents/"): return "Portable skills"
    if raw.startswith("iOS/workflow/"): return "iOS harness"
    if raw.startswith("Android/workflow/"): return "Android harness"
    if raw in {"specs/product/README.md", "iOS/specs/README.md", "Android/specs/README.md"}: return "Spec schema indexes"
    if raw.startswith((".codex/", ".claude/", ".cursor/", ".opencode/")): return "Runtime adapters"
    if "hook" in raw: return "Git hooks"
    if "NOTICE" in raw or raw.startswith("third_party/"): return "Notices"
    return "Root entrypoints"


def escape_table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def markdown_link(raw: str) -> str:
    return f"[`{raw}`]({raw})"


def render_readme_capabilities(root: Path, platforms: dict[str, dict[str, object]]) -> str:
    lines = [
        "| Клиент | Source/build roots | Platform specs | Capabilities | Addenda | Rules |",
        "|---|---|---|---|---:|---:|",
    ]
    for platform, adapter in platforms.items():
        source = ", ".join(markdown_link(item) for item in discover_source_roots(root, platform))
        package_root = str(adapter["package_root"]) + "/"
        capabilities = " → ".join(f"`{item}`" for item in adapter["lifecycle_capabilities"])
        phases = root / platform / "workflow/phases"
        rules = root / platform / "workflow/rules"
        lines.append(
            f"| {platform} | {source} | {markdown_link(package_root)} | {capabilities} | "
            f"{len(list(phases.glob('*.md')))} | {len(list(rules.rglob('*.md')))} |"
        )
    return "\n".join(lines)


def render_skill_matrix(root: Path, skills: dict[str, dict[str, object]]) -> str:
    lines = [
        "| Skill | Назначение | Каноническая phase | Пишет | Verification |",
        "|---|---|---|---|---|",
    ]
    for name, skill in skills.items():
        metadata = skill["phase_metadata"]
        writes = metadata.get("writes_artifacts", [])
        writes_text = ", ".join(f"`{item}`" for item in writes) if isinstance(writes, list) and writes else "нет"
        lines.append(
            f"| `{name}` | {escape_table(skill['description'])} | "
            f"{markdown_link(repo_path(skill['phase'], root))} | {escape_table(writes_text)} | "
            f"`{escape_table(metadata.get('requires_verification', 'not-declared'))}` |"
        )
    return "\n".join(lines)


def render_deep_wiring(root: Path, skills: dict[str, dict[str, object]], platforms: dict[str, dict[str, object]]) -> str:
    lines = [
        "### Skill call graph",
        "",
        "| Skill | Common phase | Recommended roles | Artifact contract |",
        "|---|---|---|---|",
    ]
    for name, skill in skills.items():
        metadata = skill["phase_metadata"]
        roles = metadata.get("recommended_roles", [])
        writes = metadata.get("writes_artifacts", [])
        roles_text = ", ".join(f"`{item}`" for item in roles) if isinstance(roles, list) and roles else "—"
        writes_text = ", ".join(f"`{item}`" for item in writes) if isinstance(writes, list) and writes else "read-only"
        lines.append(f"| `{name}` | {markdown_link(repo_path(skill['phase'], root))} | {escape_table(roles_text)} | {escape_table(writes_text)} |")
    lines.extend([
        "",
        "### Platform adapter projection",
        "",
        "| Platform | Adapter | Capabilities | Phase profiles | Scope profiles | Addenda | Rules | Roles |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ])
    for platform, adapter in platforms.items():
        base = root / platform / "workflow"
        lines.append(
            f"| {platform} | {markdown_link(repo_path(base / 'platform-contract.json', root))} | "
            f"{escape_table(', '.join(str(item) for item in adapter['lifecycle_capabilities']))} | "
            f"{len(adapter['phase_rule_profiles'])} | {len(adapter.get('scope_rule_profiles', {}))} | "
            f"{len(list((base / 'phases').glob('*.md')))} | {len(list((base / 'rules').rglob('*.md')))} | "
            f"{len(list((base / 'roles').glob('*.md')))} |"
        )
    return "\n".join(lines)


def render_inventory(root: Path) -> str:
    files = inventory_files(root)
    grouped: dict[str, list[Path]] = {}
    for path in files:
        grouped.setdefault(category(path, root), []).append(path)
    lines: list[str] = []
    for group in sorted(grouped):
        lines.extend([f"### {group}", "", "| Path | Purpose |", "|---|---|"])
        for path in grouped[group]:
            raw = repo_path(path, root)
            lines.append(f"| {markdown_link(raw)} | {escape_table(file_purpose(path, root))} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_runtime_parity(root: Path, skills: dict[str, dict[str, object]]) -> str:
    role_count = len(canonical_roles(root))
    lines = [
        "| Runtime | Skill discovery | Skill entry coverage | Role bindings | Hook/config binding |",
        "|---|---|---:|---:|---|",
    ]
    for runtime, spec in RUNTIME_SPECS.items():
        command_dir = spec["commands"]
        command_count = len(list((root / str(command_dir)).glob("*.md"))) if command_dir else len(skills)
        entry_kind = "thin" if command_dir else "native"
        binding = str(spec["binding"])
        lines.append(
            f"| {runtime} | {markdown_link(str(spec['skills']))} | {entry_kind} {command_count}/{len(skills)} | "
            f"{len(runtime_role_names(root, str(spec['roles'])))}/{role_count} | {markdown_link(binding)} |"
        )
    lines.extend([
        "",
        f"Portable skills: **{len(skills)}**. Canonical/runtime roles: **{role_count}** per runtime.",
        "Claude Code и OpenCode имеют thin command для каждого skill; Codex и Cursor используют native discovery portable SSOT.",
    ])
    return "\n".join(lines)


def generated_bodies(root: Path) -> tuple[dict[str, str], dict[str, int]]:
    for raw in REQUIRED_DOCUMENTATION_SURFACES:
        if not (root / raw).is_file():
            raise DocsError(f"{raw}: required documentation surface is missing")
    skills = load_skills(root)
    platforms = load_platforms(root)
    validate_runtime_bindings(root, set(skills))
    files = inventory_files(root)
    bodies = {
        "README_CAPABILITIES": render_readme_capabilities(root, platforms),
        "WORKFLOW_SKILLS": render_skill_matrix(root, skills),
        "DEEP_WIRING": render_deep_wiring(root, skills, platforms),
        "DEEP_INVENTORY": render_inventory(root),
        "DEEP_RUNTIME_PARITY": render_runtime_parity(root, skills),
    }
    coverage = {
        "portable_skills": len(skills),
        "common_phases": len(list((root / "workflow/phases").glob("*.md"))),
        "common_rules": len(list((root / "workflow/rules").rglob("*.md"))),
        "common_roles": len(list((root / "workflow/roles").glob("*.md"))),
        "scripts": sum(path.is_file() for path in (root / "workflow/scripts").glob("*")),
        "templates": sum(path.is_file() for path in (root / "workflow/templates").glob("*")),
        "platforms": len(platforms),
        "inventory_files": len(files),
        "runtime_command_bindings": sum(
            len(list((root / str(spec["commands"])).glob("*.md")))
            for spec in RUNTIME_SPECS.values() if spec["commands"]
        ),
        "runtime_role_bindings": sum(
            len(runtime_role_names(root, str(spec["roles"]))) for spec in RUNTIME_SPECS.values()
        ),
    }
    return bodies, coverage


def marker(marker_name: str, side: str) -> str:
    return f"<!-- {side} GENERATED: {marker_name} -->"


def generated_block(name: str, body: str) -> str:
    return f"{marker(name, 'BEGIN')}\n{body.rstrip()}\n{marker(name, 'END')}"


def find_block(text: str, name: str, document: str) -> tuple[int, int, str]:
    begin = marker(name, "BEGIN")
    end = marker(name, "END")
    if text.count(begin) != 1 or text.count(end) != 1:
        raise DocsError(f"{document}: marker {name} must have exactly one BEGIN and END")
    start = text.index(begin)
    finish = text.index(end, start) + len(end)
    if text.find(end) < start:
        raise DocsError(f"{document}: malformed marker order for {name}")
    return start, finish, text[start:finish]


def validate_document_markers(path: Path, expected: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    seen = MARKER_RE.findall(text)
    allowed = {(side, name) for name in expected for side in ("BEGIN", "END")}
    if set(seen) != allowed or len(seen) != len(allowed):
        raise DocsError(f"{path.name}: missing, duplicate, malformed or unknown generated marker")
    spans = []
    for name in expected:
        start, finish, _ = find_block(text, name, path.name)
        spans.append((start, finish))
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise DocsError(f"{path.name}: generated blocks overlap")


def exact_document(root: Path, name: str) -> Path:
    entries = [item for item in root.iterdir() if item.is_file()]
    exact = [item for item in entries if item.name == name]
    if len(exact) == 1:
        return exact[0]
    candidates = [item.name for item in entries if item.name.casefold() == name.casefold()]
    if candidates:
        raise DocsError(f"{name}: case mismatch; found {', '.join(sorted(candidates))}")
    raise DocsError(f"{name}: required root document is missing")


def validate_local_links(root: Path, documents: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in documents:
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = unquote(match.group(1).strip())
            target = raw.split("#", 1)[0]
            if not target or raw.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if target.startswith("/") or not (path.parent / target).resolve().exists():
                errors.append(f"{path.name}: broken or non-relative link: {raw}")
    return errors


def forbidden_prose_errors(documents: list[Path]) -> list[str]:
    errors: list[str] = []
    forbidden = (
        "jour" + "io",
        "design_system_" + "helper",
    )
    absolute = re.compile(r"(?:file://|/(?:Users|home)/[^\s)`]+)", re.IGNORECASE)
    for path in documents:
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()
        if any(token.casefold() in lowered for token in forbidden):
            errors.append(f"{path.name}: forbidden source-project name")
        if absolute.search(text):
            errors.append(f"{path.name}: local absolute path is forbidden")
    return errors


def check_repository(root: Path) -> dict[str, object]:
    root = root.resolve()
    errors: list[str] = []
    documents: list[Path] = []
    try:
        for name, expected in DOC_BLOCKS.items():
            path = exact_document(root, name)
            validate_document_markers(path, expected)
            documents.append(path)
        bodies, coverage = generated_bodies(root)
        for path in documents:
            for name in DOC_BLOCKS[path.name]:
                _, _, actual = find_block(path.read_text(encoding="utf-8"), name, path.name)
                expected = generated_block(name, bodies[name])
                if actual != expected:
                    errors.append(f"{path.name}: generated block {name} is stale")
        errors.extend(validate_local_links(root, documents))
        errors.extend(forbidden_prose_errors(documents))
    except (DocsError, OSError) as error:
        errors.append(str(error))
        coverage = {}
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "coverage": coverage,
    }


def render_repository(root: Path) -> dict[str, object]:
    root = root.resolve()
    documents = {name: exact_document(root, name) for name in DOC_BLOCKS}
    for name, path in documents.items():
        validate_document_markers(path, DOC_BLOCKS[name])
    bodies, coverage = generated_bodies(root)
    changed: list[str] = []
    for name, path in documents.items():
        text = path.read_text(encoding="utf-8")
        replacements: list[tuple[int, int, str]] = []
        for block_name in DOC_BLOCKS[name]:
            start, finish, _ = find_block(text, block_name, name)
            replacements.append((start, finish, generated_block(block_name, bodies[block_name])))
        updated = text
        for start, finish, replacement in sorted(replacements, reverse=True):
            updated = updated[:start] + replacement + updated[finish:]
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(name)
    result = check_repository(root)
    if result["status"] != "PASS":
        raise DocsError("render produced invalid documentation: " + "; ".join(result["errors"]))
    return {"status": "PASS", "changed": changed, "coverage": coverage}


def outside_generated(text: str, document: str) -> str:
    result = text
    for name in DOC_BLOCKS[document]:
        start, finish, _ = find_block(result, name, document)
        result = result[:start] + f"<GENERATED:{name}>" + result[finish:]
    return result


def copy_fixture(source: Path, target: Path) -> None:
    for raw in INVENTORY_DIRS:
        source_path = source / raw
        if source_path.is_dir():
            shutil.copytree(source_path, target / raw)
    for raw in INVENTORY_ROOT_FILES:
        source_path = source / raw
        if source_path.is_file():
            destination = target / raw
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)
    ios_project = target / "iOS/SysDevScen/Sample.xcodeproj/project.pbxproj"
    ios_project.parent.mkdir(parents=True, exist_ok=True)
    ios_project.write_text("fixture\n", encoding="utf-8")
    android_module = target / "Android/app"
    (android_module / "src").mkdir(parents=True, exist_ok=True)
    (android_module / "build.gradle.kts").write_text("// fixture\n", encoding="utf-8")
    for directory in (target / "specs/product", target / "iOS/specs", target / "Android/specs"):
        directory.mkdir(parents=True, exist_ok=True)


def assert_failed(root: Path, token: str) -> None:
    result = check_repository(root)
    assert result["status"] == "FAIL", result
    assert any(token in error for error in result["errors"]), result


def self_test(root: Path) -> int:
    with tempfile.TemporaryDirectory() as temporary:
        fixture = Path(temporary).resolve()
        copy_fixture(root, fixture)
        render_repository(fixture)
        bodies, _ = generated_bodies(fixture)
        assert "| iOS |" in bodies["README_CAPABILITIES"]
        assert "| Android |" in bodies["README_CAPABILITIES"]
        assert "iOS/workflow/phases/verify.md" in bodies["DEEP_INVENTORY"]
        assert "Android/workflow/phases/verify.md" in bodies["DEEP_INVENTORY"]
        for raw in ("specs/product/README.md", "iOS/specs/README.md", "Android/specs/README.md"):
            assert raw in bodies["DEEP_INVENTORY"], f"stable schema index missing: {raw}"

        transient_metadata = (
            "workflow/.DS_Store",
            ".agents/Thumbs.db",
            "Android/workflow/desktop.ini",
            ".opencode/.gitignore",
            ".opencode/bun.lock",
            ".opencode/package-lock.json",
            ".opencode/package.json",
            "workflow/archive-requests/legacy-retirement.json",
        )
        for raw in transient_metadata:
            path = fixture / raw
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("transient metadata\n", encoding="utf-8")
        assert check_repository(fixture)["status"] == "PASS", "filesystem metadata staled documentation"
        inventory = generated_bodies(fixture)[0]["DEEP_INVENTORY"]
        assert not any(raw in inventory for raw in transient_metadata), "filesystem metadata entered inventory"
        assert check_repository(fixture)["status"] == "PASS"

        missing = fixture / "workflow.md"
        saved = missing.read_bytes(); missing.unlink()
        assert_failed(fixture, "required root document is missing")
        missing.write_bytes(saved)
        wrong_case = fixture / "Workflow.md"; missing.rename(wrong_case)
        assert_failed(fixture, "case mismatch")
        wrong_case.rename(missing)

        readme = fixture / "README.md"
        clean = readme.read_text(encoding="utf-8")
        readme.write_text(clean.replace("<!-- END GENERATED: README_CAPABILITIES -->", "<!-- BEGIN GENERATED: README_CAPABILITIES -->\n<!-- END GENERATED: README_CAPABILITIES -->", 1), encoding="utf-8")
        assert_failed(fixture, "duplicate")
        readme.write_text(clean, encoding="utf-8")
        readme.write_text(clean.replace("| iOS |", "| changed |", 1), encoding="utf-8")
        assert_failed(fixture, "stale")
        readme.write_text(clean, encoding="utf-8")

        manual_before = {name: outside_generated((fixture / name).read_text(encoding="utf-8"), name) for name in DOC_BLOCKS}
        inventory_marker = marker("DEEP_INVENTORY", "BEGIN")
        deep = fixture / "deep-info.md"
        deep.write_text(deep.read_text(encoding="utf-8").replace(inventory_marker, inventory_marker + "\nmanual generated edit", 1), encoding="utf-8")
        assert_failed(fixture, "stale")
        render_repository(fixture)
        manual_after = {name: outside_generated((fixture / name).read_text(encoding="utf-8"), name) for name in DOC_BLOCKS}
        assert manual_before == manual_after, "render changed manual prose"
        once = {name: (fixture / name).read_bytes() for name in DOC_BLOCKS}
        assert render_repository(fixture)["changed"] == [], "render must be idempotent"
        assert once == {name: (fixture / name).read_bytes() for name in DOC_BLOCKS}

        additions = (
            ("workflow/rules/fixture-rule.md", "# Fixture rule\n"),
            ("workflow/scripts/fixture-script.py", '"""Fixture script."""\n'),
            ("workflow/phases/fixture-phase.md", "---\nphase: fixture-phase\nwrites_artifacts:\nrequires_verification: focused\nrecommended_roles:\n---\n\n# Fixture phase\n"),
            ("iOS/workflow/phases/fixture-addendum.md", "# iOS fixture addendum\n"),
            ("Android/workflow/phases/fixture-addendum.md", "# Android fixture addendum\n"),
            (".cursor/runtime-binding.md", "# Fixture runtime binding\n"),
        )
        for raw, content in additions:
            path = fixture / raw; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            assert_failed(fixture, "stale")
            render_repository(fixture)

        skill = fixture / ".agents/skills/fixture-skill"
        (skill / "agents").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: fixture-skill\ndescription: Проверить fixture skill.\n---\n\n# Fixture skill\n", encoding="utf-8")
        (skill / "agents/openai.yaml").write_text("interface:\n  display_name: Fixture\n", encoding="utf-8")
        (fixture / "workflow/phases/fixture-skill.md").write_text("---\nphase: fixture-skill\nwrites_artifacts:\nrequires_verification: focused\nrecommended_roles:\n---\n\n# Fixture skill phase\n", encoding="utf-8")
        for runtime in (".claude", ".opencode"):
            command = fixture / runtime / "commands/fixture-skill.md"
            command.write_text("---\ndescription: Fixture command\n---\n\nUse `.agents/skills/fixture-skill/SKILL.md`.\n", encoding="utf-8")
        assert_failed(fixture, "stale")
        render_repository(fixture)

        adapter_path = fixture / "Android/workflow/platform-contract.json"
        adapter = load_json(adapter_path)
        adapter["lifecycle_capabilities"] = adapter["lifecycle_capabilities"][:-1]
        adapter_path.write_text(json.dumps(adapter), encoding="utf-8")
        assert_failed(fixture, "README.md: generated block README_CAPABILITIES is stale")
        render_repository(fixture)

        (fixture / "iOS/specs/transient/changes/current/meta.json").parent.mkdir(parents=True)
        (fixture / "iOS/specs/transient/changes/current/meta.json").write_text("{}\n", encoding="utf-8")
        native = fixture / "Android/app/src/main/java/Transient.kt"; native.parent.mkdir(parents=True, exist_ok=True)
        native.write_text("class Transient\n", encoding="utf-8")
        assert check_repository(fixture)["status"] == "PASS", "transient specs/native source entered inventory"
        transient_inventory = generated_bodies(fixture)[0]["DEEP_INVENTORY"]
        assert "iOS/specs/transient/changes/current/meta.json" not in transient_inventory
        assert "Android/app/src/main/java/Transient.kt" not in transient_inventory

        workflow_doc = fixture / "workflow.md"
        clean_workflow = workflow_doc.read_text(encoding="utf-8")
        workflow_doc.write_text(clean_workflow + "\n[broken](missing.md)\n", encoding="utf-8")
        assert_failed(fixture, "broken")
        workflow_doc.write_text(clean_workflow + "\nLocal: /" + "Users/example/repo\n", encoding="utf-8")
        assert_failed(fixture, "absolute")
        workflow_doc.write_text(clean_workflow + "\n" + "jour" + "io\n", encoding="utf-8")
        assert_failed(fixture, "forbidden source-project name")
        workflow_doc.write_text(clean_workflow, encoding="utf-8")

        broken_command = fixture / ".claude/commands/fixture-skill.md"
        original_command = broken_command.read_text(encoding="utf-8")
        broken_command.write_text(original_command.replace(".agents/skills/fixture-skill/SKILL.md", "missing"), encoding="utf-8")
        assert_failed(fixture, "portable skill binding is missing")
        broken_command.write_text(original_command, encoding="utf-8")
        phase_path = fixture / "workflow/phases/fixture-skill.md"
        original_phase = phase_path.read_text(encoding="utf-8")
        phase_path.write_text(original_phase.replace("phase: fixture-skill", "malformed frontmatter"), encoding="utf-8")
        assert_failed(fixture, "malformed frontmatter line")
        phase_path.write_text(original_phase, encoding="utf-8")
        adapter_path.write_text("{", encoding="utf-8")
        assert_failed(fixture, "invalid JSON")
    print("harness-docs self-test: PASS (markers, freshness, parity, isolation)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repository_root())
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--json", action="store_true", dest="as_json")
    check_parser.add_argument("--root", type=Path, dest="command_root")
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--root", type=Path, dest="command_root")
    args = parser.parse_args()
    root = getattr(args, "command_root", None) or args.root
    if args.self_test:
        return self_test(root.resolve())
    if args.command == "check":
        result = check_repository(root)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Harness docs: {result['status']}")
            for error in result["errors"]:
                print(f"- {error}")
        return 0 if result["status"] == "PASS" else 2
    if args.command == "render":
        try:
            result = render_repository(root)
        except (DocsError, OSError) as error:
            print(f"Harness docs render: FAIL\n- {error}")
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    parser.error("command render/check or --self-test is required")
    return 2


if __name__ == "__main__":
    sys.exit(main())
