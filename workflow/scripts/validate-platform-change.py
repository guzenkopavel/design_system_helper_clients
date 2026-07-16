#!/usr/bin/env python3
"""Fail-closed validator for adapter-backed platform change packages."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path

import platform_rule_profiles as rule_profiles
import artifact_language
import platform_path_ownership as path_ownership

from platform_rule_profiles import (
    ARTIFACT_LANGUAGE_RULE,
    CURRENT_MODULARITY_CONTRACT_VERSION,
    LEGACY_REGISTRY_PATH,
    LEGACY_MODULARITY_CONTRACT_VERSION,
    RuleProfileError,
    applicable_rules,
    legacy_package_hashes,
    semantic_projection,
    require_capability,
    resolve_package_contract_version,
    validate_capabilities,
    validate_pre_commit_profile,
    validate_profiles,
    scope_task_checks_for_version,
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_RE = re.compile(r"^task-\d{3}$")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|<[^>\n]+>|\{\{|\}\}|\.\.\.", re.I)
DELIVERABLE_ACTION_RE = re.compile(
    r"^(?:реализова|выполн|созда|добав|сдела|подготов|обнов)\w*$"
    r"|^(?:implement|complet|creat|add|prepar|updat)\w*$"
    r"|^do(?:es|ing|ne)?$",
    re.I,
)
DELIVERABLE_GENERIC_WORD_RE = re.compile(
    r"^(?:необходим|требуем|нужн|соответствующ|нов|текущ|планов|базов|минимальн|"
    r"задач|работ|изменен|проект|файл|тест|проверк|результат|артефакт|код|реализац|"
    r"конфигурац|настройк|продукт|контракт)\w*$"
    r"|^(?:the|a|an|this|that|in|on|for|of|to|and|with|as|"
    r"all|necessary|required|needed|appropriate|new|current|planned|relevant|basic|minimal|"
    r"task|work|change|project|file|test|check|result|artifact|code|implementation|"
    r"configuration|config|outcome|product|contract)s?$"
    r"|^(?:в|на|для|по|и|с|к|из|как|эту|этот|эти|все|вся|весь)$",
    re.I,
)
DELIVERABLE_ID_RE = re.compile(
    r"\b(?:[a-z][a-z0-9]*-)*(?:req|ac)-[a-z0-9]+\b|\btask-[0-9]{3}\b",
    re.I,
)
DELIVERABLE_PATH_RE = re.compile(
    r"(?<![\w.-])(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+"
    r"|\b[A-Za-z0-9_.-]+\.(?:swift|kt|kts|java|m|mm|h|json|ya?ml|toml|xml|gradle|md)\b",
    re.I,
)
DELIVERABLE_PROSE_MIN_WORDS = 4
DELIVERABLE_PROSE_MIN_LETTERS = 24
DELIVERABLE_INTERNAL_JOINERS = frozenset("-'’ʼ‐‑‒–—")
DELIVERABLE_FRAGMENT_SEPARATOR_CLASS = r"\-\u2010\u2011\u2012\u2013\u2014\./\\'\u2019\u02bc"
PLATFORM_UX_UNRESOLVED_RE = re.compile(r"\b(?:UNKNOWN|GAPS?|PENDING|UNRESOLVED)\b", re.I)
SHARED_REQ_RE = re.compile(r"(?m)^-\s+`(REQ-[A-Za-z0-9_-]+)`\s+[—-]\s+(.+)$")
SHARED_AC_RE = re.compile(r"(?m)^-\s+`(AC-[A-Za-z0-9_-]+)`\s+[—-]\s+(.+)$")
SHARED_COPY_RE = re.compile(r"(?m)^(?:###\s+|-\s+`?)(?:REQ|AC)-[A-Za-z0-9_-]+`?\s+[—-]")
REQUIRED_META = {
    "platform", "feature", "change_id", "change_type", "tier", "status",
    "shared_product_spec", "product_status", "product_approval",
    "product_impact", "impact_evidence", "blocking_questions", "problems",
    "design_gate", "tasks_total", "tasks_done", "verification_status",
    "verified_at", "verification_state",
    "engineering_scopes", "applicable_rule_files", "rule_selection_snapshot",
    "modularity_contract_version",
}
MODULARITY_FIELDS = (
    "Outcome", "Capability triggers", "Physical boundaries",
    "Public contracts and dependency direction", "App-shell responsibilities",
    "App-shell capability ownership",
    "Repository evidence", "Rationale and trade-offs",
    "Migration boundary and trigger", "Over-modularization check",
    "Boundary guard verdict",
)
MODULARITY_OUTCOMES = {"isolated", "deviation", "not-applicable"}
CAPABILITY_TRIGGERS_RE = re.compile(
    r"^independent-feature=(yes|no); domain-data=(yes|no); network=(yes|no); "
    r"persistence=(yes|no); reusable-ui=(yes|no); consumers=([0-9]+); "
    r"independent-ownership=(yes|no)$"
)
APP_SHELL_RESPONSIBILITIES = (
    "entry-points, lifecycle, root-routing, dependency-wiring, "
    "platform-configuration, target-resources"
)
MODULARITY_VERIFICATION_FIELDS = (
    "Dependency graph", "Public API and visibility", "Module-level tests",
    "Consumer integration and build", "App-shell allowlist",
)
COMMON_DESIGN = (
    "Current context", "Proposed architecture and boundaries",
    "Data and control flow", "Error and recovery model", "Verification strategy",
)
TERMINAL_MODES = {"verify", "archive"}
NATIVE_OBLIGATION_IDS = (
    "NATIVE-APPEARANCE",
    "NATIVE-LIGHT",
    "NATIVE-DARK",
    "NATIVE-INCREASED-CONTRAST",
    "NATIVE-ASSISTIVE-SEMANTICS",
    "NATIVE-TEXT-SCALING",
    "NATIVE-MOTION",
    "NATIVE-DEVICE-ADAPTATION",
    "NATIVE-AVAILABILITY-FALLBACK",
)
NATIVE_OBSERVATION_KEYS = {
    "schema_version", "obligation_id", "status", "observation", "evidence_refs",
}
PLATFORM_UX_KEYS = {"role", "artifact", "design_language", "required_terms", "task_checks"}
PLATFORM_UX_HEADINGS = (
    "Evidence inspected", "Shared intent mapping",
    "Information architecture and navigation", "Component and state mapping",
    "Native visual language", "Color roles and appearance",
    "Accessibility and localization", "Motion and interaction",
    "Device and layout adaptation", "Fallback and availability",
    "Verification scenarios", "Open gaps",
)
TASK_AUTHORED_REPORT_RE = re.compile(r"^task-[0-9]{3}\.md$")
RECONCILIATION_AUTHORED_REPORT_RE = re.compile(
    r"^reconciliation-[0-9]{8}T[0-9]{6}Z-task-[0-9]{3}(?:-[a-z0-9-]+)?\.md$"
)
_PRODUCT_VALIDATOR = None


class AdapterError(ValueError):
    pass


def load_product_validator():
    global _PRODUCT_VALIDATOR
    if _PRODUCT_VALIDATOR is not None:
        return _PRODUCT_VALIDATOR
    path = Path(__file__).with_name("validate-product-spec.py")
    spec = importlib.util.spec_from_file_location("platform_product_validator", path)
    if spec is None or spec.loader is None:
        raise AdapterError("cannot load validate-product-spec.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    _PRODUCT_VALIDATOR = module
    return module


def validate_product_ready(repo: Path, feature: str) -> list[str]:
    try:
        return load_product_validator().check_product(repo, feature)
    except (OSError, ValueError) as error:
        return [f"product review gate failed: {error}"]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


_language_residual = artifact_language.language_residual
_authored_language_blocks = artifact_language.authored_markdown_blocks
validate_authored_markdown_language = artifact_language.validate_authored_markdown_language
validate_task_evidence_language = artifact_language.validate_task_evidence_language


def typed_authored_report_paths(package: Path) -> list[Path]:
    evidence = package / "evidence"
    if not evidence.is_dir():
        return []
    try:
        children = sorted(evidence.iterdir(), key=lambda item: item.name)
    except OSError:
        return []
    return [
        child for child in children
        if TASK_AUTHORED_REPORT_RE.fullmatch(child.name)
        or RECONCILIATION_AUTHORED_REPORT_RE.fullmatch(child.name)
    ]


def is_subpath(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def safe_repo_path(repo: Path, raw: str, label: str) -> Path:
    value = Path(raw)
    if value.is_absolute() or ".." in value.parts:
        raise AdapterError(f"{label} must be a safe repo-relative path")
    result = (repo / value).resolve()
    if not is_subpath(result, repo):
        raise AdapterError(f"{label} escapes repository root")
    return result


def load_adapter(repo: Path, platform: str) -> dict[str, object]:
    matches: list[dict[str, object]] = []
    for path in sorted(repo.glob("*/workflow/platform-contract.json")):
        try:
            data = json.loads(read(path))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("platform_input", "")).casefold() == platform.casefold():
            data["_path"] = path.relative_to(repo).as_posix()
            matches.append(data)
    if not matches:
        raise AdapterError(
            f"NOT IMPLEMENTED: platform '{platform}' has no implementation adapter; no files were written"
        )
    if len(matches) != 1:
        raise AdapterError(f"platform '{platform}' has multiple adapters")
    adapter = matches[0]
    required = {
        "platform_input", "platform_name", "platform_root", "package_root",
        "active_changes_namespace", "archive_namespace", "production_roots",
        "protected_roots", "production_exclusions", "contract_prefix",
        "boundary_guard", "extended_design_sections", "ui_task_checks", "rule_files",
        "phase_rule_profiles", "scope_rule_profiles", "scope_task_checks",
        "context_file_suffixes", "context_excluded_directories",
        "context_always_include_globs",
        "lifecycle_capabilities",
        "pre_commit",
        "platform_ux",
        "modularity",
    }
    missing = sorted(required - set(adapter))
    if missing:
        raise AdapterError(f"platform adapter missing fields: {', '.join(missing)}")
    for field in ("platform_root", "package_root"):
        safe_repo_path(repo, str(adapter[field]), field)
    for field in ("production_roots", "protected_roots", "production_exclusions", "rule_files"):
        value = adapter[field]
        if not isinstance(value, list) or not value:
            raise AdapterError(f"{field} must be a non-empty list")
        for raw in value:
            safe_repo_path(repo, str(raw), field)
    for field in ("active_changes_namespace", "archive_namespace"):
        if not SLUG_RE.fullmatch(str(adapter[field])):
            raise AdapterError(f"{field} must be strict kebab-case")
    if not re.fullmatch(r"[A-Z][A-Z0-9]*", str(adapter["contract_prefix"])):
        raise AdapterError("contract_prefix must be uppercase alphanumeric")
    suffixes = adapter["context_file_suffixes"]
    if (
        not isinstance(suffixes, list) or not suffixes
        or not all(isinstance(item, str) and re.fullmatch(r"\.[a-z0-9]+", item) for item in suffixes)
        or len(suffixes) != len(set(suffixes))
    ):
        raise AdapterError("context_file_suffixes must be a unique non-empty list of lowercase extensions")
    excluded = adapter["context_excluded_directories"]
    if (
        not isinstance(excluded, list)
        or not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9._-]+", item) for item in excluded)
        or len(excluded) != len(set(excluded))
    ):
        raise AdapterError("context_excluded_directories must be a unique list of directory names")
    globs = adapter["context_always_include_globs"]
    if not isinstance(globs, list) or not globs:
        raise AdapterError("context_always_include_globs must be a non-empty list")
    for pattern in globs:
        if (
            not isinstance(pattern, str) or Path(pattern).is_absolute()
            or ".." in Path(pattern).parts
            or not re.fullmatch(r"[A-Za-z0-9_./*?-]+", pattern)
        ):
            raise AdapterError(f"unsafe context_always_include_globs pattern: {pattern}")
    try:
        _catalog, _phases, scopes = validate_profiles(repo, adapter)
        validate_pre_commit_profile(adapter)
    except RuleProfileError as error:
        raise AdapterError(str(error)) from error
    task_checks = adapter["scope_task_checks"]
    if not isinstance(task_checks, dict) or set(task_checks) - set(scopes):
        raise AdapterError("scope_task_checks keys must be known engineering scopes")
    for scope, checks in task_checks.items():
        if (
            not isinstance(checks, list) or not checks
            or not all(isinstance(item, str) and item.strip() for item in checks)
            or len(checks) != len(set(checks))
        ):
            raise AdapterError(f"scope_task_checks.{scope} must be a unique non-empty list")
    if task_checks.get("ui") != adapter["ui_task_checks"]:
        raise AdapterError("scope_task_checks.ui must exactly match ui_task_checks")
    platform_ux = adapter["platform_ux"]
    if not isinstance(platform_ux, dict) or set(platform_ux) != PLATFORM_UX_KEYS:
        raise AdapterError("platform_ux must use the exact nested schema")
    if not SLUG_RE.fullmatch(str(platform_ux.get("role", ""))):
        raise AdapterError("platform_ux.role must be a strict role slug")
    if platform_ux.get("artifact") != "platform-ux.md":
        raise AdapterError("platform_ux.artifact must be exactly platform-ux.md")
    design_language = str(platform_ux.get("design_language", "")).strip()
    if len(design_language) < 3 or PLACEHOLDER_RE.search(design_language):
        raise AdapterError("platform_ux.design_language must be substantive")
    for field in ("required_terms", "task_checks"):
        values = platform_ux.get(field)
        if (
            not isinstance(values, list) or not values
            or not all(isinstance(item, str) and item.strip() for item in values)
            or len(values) != len(set(values))
        ):
            raise AdapterError(f"platform_ux.{field} must be a unique non-empty list")
    return adapter


def changes_root(repo: Path, adapter: dict[str, object], feature: str) -> Path:
    root = safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    return root / feature / str(adapter["active_changes_namespace"])


def active_change_ids(repo: Path, adapter: dict[str, object], feature: str) -> list[str]:
    root = changes_root(repo, adapter, feature)
    if not root.is_dir():
        return []
    return sorted(
        item.name for item in root.iterdir()
        if item.is_dir() and SLUG_RE.fullmatch(item.name)
        and (item / "meta.json").is_file() and not (item / "ARCHIVED.md").exists()
    )


def active_change_inventory(
    repo: Path, adapter: dict[str, object], feature: str,
) -> tuple[list[str], list[str]]:
    root = changes_root(repo, adapter, feature)
    if not root.is_dir():
        return [], []
    active: list[str] = []
    partial: list[str] = []
    for item in sorted(root.iterdir(), key=lambda value: value.name):
        if item.is_symlink() or not item.is_dir() or not SLUG_RE.fullmatch(item.name):
            partial.append(item.name)
            continue
        children = sorted(child.name for child in item.iterdir())
        tombstone = item / "ARCHIVED.md"
        if children == ["ARCHIVED.md"] and tombstone.is_file() and not tombstone.is_symlink():
            continue
        meta = item / "meta.json"
        if not tombstone.exists() and meta.is_file() and not meta.is_symlink():
            active.append(item.name)
        else:
            partial.append(item.name)
    return active, partial


def resolve_change(
    repo: Path, adapter: dict[str, object], feature: str,
    change: str | None, mode: str,
) -> tuple[str, Path]:
    if not SLUG_RE.fullmatch(feature):
        raise AdapterError("feature must be a strict kebab-case slug")
    if change is None:
        if mode == "propose":
            change = feature
        else:
            active, partial = active_change_inventory(repo, adapter, feature)
            if len(active) != 1 or partial:
                raise AdapterError(
                    "omitted --change requires exactly one classified active package; "
                    f"found {len(active)} active and {len(partial)} partial/unclassified sibling(s)"
                )
            change = active[0]
    if not SLUG_RE.fullmatch(change):
        raise AdapterError("change_id must be a strict kebab-case slug")
    root = changes_root(repo, adapter, feature).resolve()
    package = (root / change).resolve()
    if package.parent != root or not is_subpath(package, root):
        raise AdapterError("change_id escapes active package root")
    return change, package


def active_task_path_owners(
    repo: Path, adapter: dict[str, object], candidates: list[str],
) -> dict[str, list[str]]:
    """Return active package identities whose task Paths overlap each candidate."""
    root = safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    owners: dict[str, set[str]] = {raw: set() for raw in candidates}
    if not root.is_dir():
        return {raw: [] for raw in candidates}
    namespace = str(adapter["active_changes_namespace"])
    for meta_path in sorted(root.glob(f"*/{namespace}/*/meta.json")):
        package = meta_path.parent
        if (package / "ARCHIVED.md").exists():
            continue
        try:
            meta = json.loads(read(meta_path))
        except (OSError, json.JSONDecodeError):
            continue
        if meta.get("status") not in {"planned", "implementing", "verified"}:
            continue
        tasks, _errors = parse_tasks(repo, package, require_boundary_owner=False)
        identity = package.relative_to(repo).as_posix()
        for task in tasks:
            for _kind, declared in task.get("paths", []):
                for candidate in candidates:
                    if paths_overlap(str(declared), candidate):
                        owners[candidate].add(identity)
    return {raw: sorted(values) for raw, values in owners.items()}


def section(text: str, heading: str) -> str | None:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", text)
    return match.group(1).strip() if match else None


def substantive(value: str | None, minimum: int = 12) -> bool:
    if value is None or PLACEHOLDER_RE.search(value):
        return False
    cleaned = re.sub(r"[`*_#|>\-]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return len(cleaned) >= minimum and len(cleaned.split()) >= 2 and cleaned.casefold() not in {
        "n/a", "none", "нет", "pending", "not applicable",
    }


def markdown_lines_outside_fences(text: str) -> list[tuple[int, str]]:
    """Return raw-indentation lines outside top-level fences and blockquotes."""
    result: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None
    for index, line in enumerate(text.splitlines(keepends=True)):
        raw = line.rstrip("\r\n")
        if fence is not None:
            if re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{fence[1]},}}[ \t]*", raw):
                fence = None
            continue
        if re.match(r"^ {0,3}>", raw):
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", raw)
        if opening:
            marker = opening.group(1)
            fence = (marker[0], len(marker))
            continue
        result.append((index, raw))
    return result


def actual_h2_sections(text: str) -> list[tuple[str, str, int]]:
    """Parse actual column-zero H2 sections without losing body indentation."""
    lines = text.splitlines(keepends=True)
    headings: list[tuple[str, int]] = []
    for index, line in markdown_lines_outside_fences(text):
        match = re.fullmatch(r"##[ \t]+(.+?)[ \t]*", line)
        if match:
            headings.append((match.group(1), index))
    return [
        (
            heading,
            "".join(lines[index + 1:headings[position + 1][1] if position + 1 < len(headings) else len(lines)]),
            index,
        )
        for position, (heading, index) in enumerate(headings)
    ]


def implementation_deliverable_items(value: str) -> list[str]:
    """Extract only column-zero list items outside fences/blockquote."""
    result: list[str] = []
    for _index, line in markdown_lines_outside_fences(value):
        item_match = re.fullmatch(r"(?:-\s+|[0-9]+[.)]\s+)(.+?)[ \t]*", line)
        if item_match:
            result.append(item_match.group(1).strip())
    return result


def normalize_deliverable_unicode(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return "".join(
        character for character in normalized
        if unicodedata.category(character) not in {"Mn", "Me", "Cf"}
    ).casefold()


def deliverable_semantic_prose(item: str) -> str:
    prose = re.sub(r"`[^`\n]*`", " ", item)
    prose = normalize_deliverable_unicode(prose)
    prose = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", prose)
    prose = DELIVERABLE_PATH_RE.sub(" ", prose)
    prose = DELIVERABLE_ID_RE.sub(" ", prose)
    return re.sub(r"[*_#|>]", " ", prose)


def deliverable_linguistic_tokens(prose: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    for index, character in enumerate(prose):
        if character.isalpha():
            current.append(character)
            continue
        if (
            character in DELIVERABLE_INTERNAL_JOINERS and current
            and index + 1 < len(prose) and prose[index + 1].isalpha()
        ):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current)); current = []
    if current:
        tokens.append("".join(current))
    return tokens


def deliverable_token_scripts(token: str) -> set[str]:
    scripts: set[str] = set()
    for character in token:
        if not character.isalpha():
            continue
        name = unicodedata.name(character, "")
        if "CYRILLIC" in name:
            scripts.add("cyrillic")
        elif "LATIN" in name:
            scripts.add("latin")
    return scripts


def deliverable_fragment_chain(prose: str) -> bool:
    letter = r"[^\W\d_]"
    separator = rf"[\s{DELIVERABLE_FRAGMENT_SEPARATOR_CLASS}]*[{DELIVERABLE_FRAGMENT_SEPARATOR_CLASS}][\s{DELIVERABLE_FRAGMENT_SEPARATOR_CLASS}]*"
    return re.search(
        rf"(?<!{letter}){letter}(?:{separator}{letter}){{3,}}(?!{letter})",
        prose,
        flags=re.UNICODE,
    ) is not None


def deliverable_prose_analysis(item: str) -> dict[str, object]:
    prose = deliverable_semantic_prose(item)
    tokens = deliverable_linguistic_tokens(prose)
    return {
        "prose": prose,
        "tokens": tokens,
        "letters": sum(character.isalpha() for character in prose),
        "fragment_chain": deliverable_fragment_chain(prose),
        "mixed_script_tokens": [
            token for token in tokens
            if {"cyrillic", "latin"}.issubset(deliverable_token_scripts(token))
        ],
    }


def deliverable_prose_floor(analysis: dict[str, object]) -> bool:
    tokens = analysis["tokens"]
    letters = analysis["letters"]
    return (
        isinstance(tokens, list) and len(tokens) >= DELIVERABLE_PROSE_MIN_WORDS
        and isinstance(letters, int)
        and letters >= DELIVERABLE_PROSE_MIN_LETTERS
    )


def generic_deliverable(analysis: dict[str, object]) -> bool:
    tokens = analysis["tokens"]
    if not isinstance(tokens, list):
        return True
    if not tokens:
        return True
    action_positions = [index for index, token in enumerate(tokens) if DELIVERABLE_ACTION_RE.fullmatch(token)]
    if action_positions and all(
        DELIVERABLE_ACTION_RE.fullmatch(token) or DELIVERABLE_GENERIC_WORD_RE.fullmatch(token)
        for token in tokens
    ):
        return True
    return all(DELIVERABLE_GENERIC_WORD_RE.fullmatch(token) for token in tokens)


def validate_implementation_deliverables(task_name: str, body: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    sections = actual_h2_sections(body)
    deliverable_sections = [item for item in sections if item[0] == "Implementation deliverables"]
    if not deliverable_sections:
        return [], [f"{task_name} missing section: Implementation deliverables"]
    if len(deliverable_sections) != 1:
        errors.append(
            f"{task_name} Implementation deliverables section must appear exactly once"
        )
    inline_headings = [item for item in sections if item[0] == "Inline contract context"]
    steps_headings = [item for item in sections if item[0] == "Steps"]
    if (
        len(inline_headings) == 1 and len(steps_headings) == 1
        and not (inline_headings[0][2] < deliverable_sections[0][2] < steps_headings[0][2])
    ):
        errors.append(
            f"{task_name} Implementation deliverables must be between Inline contract context and Steps"
        )
    items = implementation_deliverable_items(deliverable_sections[0][1])
    if len(items) < 2:
        errors.append(
            f"{task_name} Implementation deliverables requires at least two top-level Markdown list items"
        )
    for index, item in enumerate(items, start=1):
        analysis = deliverable_prose_analysis(item)
        if not substantive(item, 12):
            errors.append(
                f"{task_name} Implementation deliverables item {index} must be substantive"
            )
        elif analysis["fragment_chain"]:
            errors.append(
                f"{task_name} Implementation deliverables item {index} contains a punctuation-separated one-letter fragment chain"
            )
        elif analysis["mixed_script_tokens"]:
            errors.append(
                f"{task_name} Implementation deliverables item {index} contains mixed Cyrillic/Latin script in one prose token"
            )
        elif not deliverable_prose_floor(analysis):
            errors.append(
                f"{task_name} Implementation deliverables item {index} requires independent prose with at least "
                f"{DELIVERABLE_PROSE_MIN_WORDS} alphabetic words and {DELIVERABLE_PROSE_MIN_LETTERS} letters"
            )
        elif generic_deliverable(analysis):
            errors.append(
                f"{task_name} Implementation deliverables item {index} is generic"
            )
    return items, errors


def explicit_none(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = re.sub(r"[`*_#|>\-]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".!;: ").casefold()
    return cleaned in {"none", "no open questions", "нет открытых вопросов"}


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^-\s*\**{re.escape(label)}\s*:\**\s*`?([^`\n]+)`?\s*$", text)
    return match.group(1).strip() if match else None


def package_contract_version(
    repo: Path, adapter: dict[str, object], meta: dict[str, object], package: Path,
    mode: str | None = None,
) -> int:
    try:
        return resolve_package_contract_version(repo, adapter, meta, package, mode)
    except RuleProfileError as error:
        raise AdapterError(str(error)) from error


def validate_modularity_decision(
    repo: Path, adapter: dict[str, object], design: str, package_scopes: set[str]
) -> list[str]:
    errors: list[str] = []
    body = section(design, "Modularity decision")
    if body is None:
        return ["design.md missing Modularity decision"]
    values: dict[str, str] = {}
    for label in MODULARITY_FIELDS:
        matches = re.findall(
            rf"(?mi)^-\s*\**{re.escape(label)}\s*:\**\s*`?([^`\n]+)`?\s*$", body
        )
        if len(matches) != 1:
            errors.append(f"Modularity decision field must appear exactly once: {label}")
            continue
        values[label] = matches[0].strip()
    for line in (item.strip() for item in body.splitlines() if item.strip()):
        if not any(
            re.match(rf"^-\s*\**{re.escape(label)}\s*:", line, re.IGNORECASE)
            for label in MODULARITY_FIELDS
        ):
            errors.append("Modularity decision allows only the exact structured field rows")
            break
    outcome = values.get("Outcome", "").casefold()
    if outcome not in MODULARITY_OUTCOMES:
        errors.append("Modularity decision Outcome must be isolated, deviation or not-applicable")
    for label in (
        "Physical boundaries", "Public contracts and dependency direction",
        "Repository evidence", "Rationale and trade-offs",
        "Migration boundary and trigger", "Over-modularization check",
    ):
        if label in values and not substantive(values[label], 24):
            errors.append(f"Modularity decision field is not substantive: {label}")
    if values.get("Boundary guard verdict") != "PASS":
        errors.append("Modularity decision requires exact Boundary guard verdict: PASS")

    trigger_match = CAPABILITY_TRIGGERS_RE.fullmatch(values.get("Capability triggers", ""))
    if trigger_match is None:
        errors.append("Modularity decision Capability triggers must use the exact machine schema")
        triggers: tuple[str, ...] = ()
        consumers = -1
        independent_ownership = "yes"
    else:
        triggers = trigger_match.groups()[:5]
        consumers = int(trigger_match.group(6))
        independent_ownership = trigger_match.group(7)
    if values.get("App-shell responsibilities") != APP_SHELL_RESPONSIBILITIES:
        errors.append("Modularity decision App-shell responsibilities must equal the exact allowlist")
    if values.get("App-shell capability ownership") != "none":
        errors.append("Modularity decision App-shell capability ownership must be exactly none")
    forbidden_shell_reference = re.compile(
        r"\b(?:app(?:['’]s)?|application(?:['’]s)?|shell|target|module)\b",
        re.IGNORECASE,
    )
    for label in (
        "Public contracts and dependency direction", "Repository evidence",
        "Rationale and trade-offs", "Migration boundary and trigger",
        "Over-modularization check",
    ):
        if forbidden_shell_reference.search(values.get(label, "")):
            errors.append(
                f"Modularity decision free-form field cannot reference app or application shell/target/module: {label}"
            )

    evidence = values.get("Repository evidence", "")
    evidence_tokens = [token.strip().strip("`") for token in evidence.split(";") if token.strip()]
    if not evidence_tokens:
        errors.append("Modularity decision requires existing repository evidence paths")
    for raw in evidence_tokens:
        value = Path(raw)
        candidate = repo / value
        if (
            value.is_absolute() or ".." in value.parts
            or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", raw)
            or candidate.is_symlink()
            or not (candidate.is_file() or candidate.is_dir())
            or not is_subpath(candidate.resolve(), repo)
        ):
            errors.append(f"Modularity decision repository evidence path is missing or unsafe: {raw}")

    physical = values.get("Physical boundaries", "")
    config = adapter.get("modularity", {})
    isolation_scope = str(config.get("isolation_scope", "")) if isinstance(config, dict) else ""
    physical_units = config.get("physical_units", []) if isinstance(config, dict) else []
    physical_remainder = physical
    for unit in sorted((str(item) for item in physical_units), key=len, reverse=True):
        physical_remainder = re.sub(re.escape(unit), "", physical_remainder, flags=re.IGNORECASE)
    if forbidden_shell_reference.search(physical_remainder):
        errors.append("Modularity decision Physical boundaries cannot reference an application unit")
    if re.search(r"\b(?:target|module|package)\b", physical_remainder, re.IGNORECASE):
        errors.append("Modularity decision Physical boundaries may name only adapter-approved unit phrases")
    if re.search(r"\b(?:folder|directory|layer|package[- ]?name|папк\w*|каталог\w*|сло[йяе]\w*)\b", physical, re.IGNORECASE):
        errors.append("Modularity decision cannot use folder/directory/layer/package-name as a physical unit")
    if outcome in {"isolated", "deviation"}:
        if isolation_scope not in package_scopes:
            errors.append(f"{outcome} Modularity decision requires engineering scope: {isolation_scope}")
        if not any(str(unit).casefold() in physical.casefold() for unit in physical_units):
            errors.append(f"{outcome} Modularity decision must name an adapter non-application physical unit")
        if re.search(r"(?<!non-)\b(?:app|application)\b.{0,24}\b(?:target|module)\b", physical, re.IGNORECASE):
            errors.append("Modularity decision physical unit must not be an application target/module")
        discovery_terms = r"\b(?:existing|discovered|proposed|существующ\w*|обнаружен\w*|предлагаем\w*)\b"
        if not re.search(discovery_terms, physical, re.IGNORECASE):
            errors.append(f"{outcome} Modularity decision must mark the physical unit existing/discovered/proposed")
    if outcome == "deviation":
        contract = values.get("Public contracts and dependency direction", "")
        migration = values.get("Migration boundary and trigger", "")
        if not re.search(r"\b(?:existing|discovered|существующ\w*|обнаружен\w*)\b", physical, re.IGNORECASE):
            errors.append("deviation requires an existing discovered non-application physical unit")
        if not re.search(r"\b(?:contract|interface|protocol|api|контракт|интерфейс|протокол)\w*\b", contract, re.IGNORECASE):
            errors.append("deviation requires a typed contract seam now")
        if not re.search(r"\b(?:when|once|after|threshold|trigger|когда|после|достижен\w*|триггер\w*)\b", migration, re.IGNORECASE):
            errors.append("deviation requires an objective migration trigger")
    elif outcome == "not-applicable":
        if trigger_match is not None and (
            any(value == "yes" for value in triggers)
            or consumers > 1
            or independent_ownership != "no"
        ):
            errors.append("not-applicable requires all capability triggers false, at most one consumer and no independent ownership")
        if not substantive(values.get("Over-modularization check"), 32):
            errors.append("not-applicable requires substantive over-modularization rationale")
    return errors


def validate_modularity_verification(verification: str, mode: str) -> list[str]:
    body = section(verification, "Modularity verification")
    if body is None:
        return ["verification.md missing Modularity verification"]
    errors: list[str] = []
    allowed = {"pending"} if mode in {"propose", "plan"} else {"pending", "PASS", "FAIL", "UNKNOWN"}
    if mode in TERMINAL_MODES:
        allowed = {"PASS"}
    for label in MODULARITY_VERIFICATION_FIELDS:
        matches = re.findall(rf"(?mi)^-\s*{re.escape(label)}:\s*(\S+)\s*$", body)
        if len(matches) != 1:
            errors.append(f"Modularity verification field must appear exactly once: {label}")
        elif matches[0] not in allowed:
            errors.append(f"Modularity verification {label} has invalid status for {mode}: {matches[0]}")
    return errors


def rule_selection_snapshot(meta: dict[str, object]) -> dict[str, object]:
    selection = {
        "engineering_scopes": meta.get("engineering_scopes"),
        "applicable_rule_files": meta.get("applicable_rule_files"),
    }
    version = meta.get("modularity_contract_version")
    if version == CURRENT_MODULARITY_CONTRACT_VERSION:
        selection["modularity_contract_version"] = version
    encoded = json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
    schema_version = 2 if version == CURRENT_MODULARITY_CONTRACT_VERSION else 1
    return {"schema_version": schema_version, **selection, "fingerprint": hashlib.sha256(encoded).hexdigest()}


def validate_rule_selection_snapshot(package: Path, meta: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if meta.get("rule_selection_snapshot") != "plan/rule-selection.json":
        return ["rule_selection_snapshot must be exactly plan/rule-selection.json after Plan"]
    path = package / "plan/rule-selection.json"
    if not path.is_file():
        return ["planned rule selection snapshot is missing"]
    try:
        recorded = json.loads(read(path))
    except (OSError, json.JSONDecodeError):
        return ["planned rule selection snapshot JSON is invalid"]
    expected = rule_selection_snapshot(meta)
    if recorded != expected:
        errors.append("planned rule selection snapshot is stale or tampered")
    return errors


def valid_human(value: str | None, minimum: int = 3) -> bool:
    if value is None or PLACEHOLDER_RE.search(value):
        return False
    clean = value.strip().strip("`* ")
    return len(clean) >= minimum and clean.casefold() not in {"none", "n/a", "pending", "unknown", "approved"}


def platform_ux_exact_none(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().strip("`*_ ").rstrip(".").strip().casefold()
    return normalized == "none"


def validate_platform_ux(
    repo: Path, adapter: dict[str, object], package: Path,
    feature: str, meta: dict[str, object], scopes: set[str],
) -> list[str]:
    config = adapter["platform_ux"]
    path = package / str(config["artifact"])
    required = meta.get("change_type") == "product-backed" and "ui" in scopes
    if not required:
        if path.exists() or path.is_symlink():
            return ["platform-ux.md is unexpected outside product-backed ui scope"]
        return []
    errors: list[str] = []
    if not path.is_file() or path.is_symlink():
        return ["product-backed ui package requires platform-ux.md"]
    body = read(path)
    if PLACEHOLDER_RE.search(body):
        errors.append("platform-ux.md contains placeholders")
    readiness_body = re.sub(r"(?mi)^##\s+Open gaps\s*$", "", body)
    if PLATFORM_UX_UNRESOLVED_RE.search(readiness_body):
        errors.append("platform-ux.md contains unresolved readiness markers")
    expected_source = f"specs/product/{feature}/ux.md"
    source = repo / expected_source
    if not source.is_file() or source.is_symlink():
        errors.append("product-backed ui package requires shared product ux.md")
    metadata = {
        "UX status": "READY",
        "Platform": str(adapter["platform_name"]),
        "Source product UX": expected_source,
        "Native design language adapter": str(config["design_language"]),
        "Color direction": "soft blue",
    }
    for label, expected in metadata.items():
        matches = re.findall(
            rf"(?mi)^-\s*\**{re.escape(label)}\s*:\**\s*`?([^`\n]+)`?\s*$", body
        )
        if len(matches) != 1:
            errors.append(f"platform-ux.md {label} metadata must appear exactly once")
        elif matches[0].strip() != expected:
            errors.append(f"platform-ux.md {label} must be exactly {expected}")
    for heading in PLATFORM_UX_HEADINGS:
        count = len(re.findall(rf"(?m)^##\s+{re.escape(heading)}\s*$", body))
        if count != 1:
            errors.append(f"platform-ux.md heading must appear exactly once: {heading}")
        elif heading != "Open gaps" and not substantive(section(body, heading), 20):
            errors.append(f"platform-ux.md missing substantive section: {heading}")
    if len(re.findall(r"(?m)^##\s+Open gaps\s*$", body)) == 1 and not platform_ux_exact_none(section(body, "Open gaps")):
        errors.append("platform-ux.md Open gaps must be exact None")
    folded = body.casefold()
    for term in config["required_terms"]:
        if str(term).casefold() not in folded:
            errors.append(f"platform-ux.md missing required native term: {term}")
    return errors


def heading_blocks(text: str, pattern: re.Pattern[str]) -> list[tuple[str, str]]:
    matches = list(pattern.finditer(text))
    result: list[tuple[str, str]] = []
    for match in matches:
        tail = text[match.end():]
        boundary = re.search(r"(?m)^#{2,3}\s+", tail)
        result.append((match.group(1), tail[:boundary.start() if boundary else None].strip()))
    return result


def parse_paths(raw: str) -> tuple[list[tuple[str, str]], list[str]]:
    result: list[tuple[str, str]] = []
    errors: list[str] = []
    tokens = [x.strip() for x in re.split(r"\s*(?:;|\|)\s*|,\s*(?=(?:existing|proposed)\s*:)", raw) if x.strip()]
    for token in tokens:
        match = re.fullmatch(r"(existing|proposed):\s*(.+)", token, re.I)
        if not match:
            errors.append("Paths token must be existing: or proposed: with a path")
            continue
        path = match.group(2).strip()
        value = Path(path)
        if not path or value.is_absolute() or ".." in value.parts:
            errors.append(f"Paths rejects empty/absolute/traversal path: {path}")
        else:
            result.append((match.group(1).casefold(), path))
    if not result:
        errors.append("Paths must contain at least one safe path")
    return result, errors


def parse_read_only_context(raw: str) -> tuple[list[str], list[str]]:
    if raw.strip().casefold() == "none":
        return [], []
    try:
        values = json.loads(raw)
    except json.JSONDecodeError:
        return [], ["Read-only context must be exact none or a JSON array of repo-relative paths"]
    if (
        not isinstance(values, list) or not values
        or not all(isinstance(item, str) and item.strip() for item in values)
        or values != sorted(set(values))
    ):
        return [], ["Read-only context must be a sorted unique non-empty JSON array"]
    errors: list[str] = []
    for value in values:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
            errors.append(f"Read-only context rejects unsafe path: {value}")
    return values, errors


def path_is_within(raw: str, roots: list[str]) -> bool:
    value = Path(raw)
    return any(value == Path(root) or Path(root) in value.parents for root in roots)


def paths_overlap(left: str, right: str) -> bool:
    lhs = Path(left); rhs = Path(right)
    return lhs == rhs or lhs in rhs.parents or rhs in lhs.parents


def parse_tasks(
    repo: Path, package: Path, require_boundary_owner: bool = True,
    adapter: dict[str, object] | None = None, validate_plan_paths: bool = False,
    require_implementation_deliverables: bool = False,
) -> tuple[list[dict[str, object]], list[str]]:
    errors: list[str] = []
    plan = package / "plan"
    files = sorted(plan.glob("task-*.md")) if plan.is_dir() else []
    expected = [f"task-{i:03d}.md" for i in range(1, len(files) + 1)]
    if [x.name for x in files] != expected:
        errors.append("plan task numbering must be continuous from task-001")
    tasks: list[dict[str, object]] = []
    task_ids = {x.stem for x in files}
    for path in files:
        body = read(path)
        if PLACEHOLDER_RE.search(body):
            errors.append(f"{path.name} contains unresolved placeholder")
        fields: dict[str, str] = {}
        field_names = ["Layer", "Engineering scopes", "Depends on", "Status", "Evidence", "Estimate (ideal)", "Paths"]
        if validate_plan_paths:
            field_names.append("Read-only context")
        if require_boundary_owner:
            field_names.insert(1, "Boundary owner")
        for name in field_names:
            match = re.search(rf"(?mi)^-\s*{re.escape(name)}:\s*(.+)$", body)
            if match:
                fields[name] = match.group(1).strip()
            else:
                errors.append(f"{path.name} missing {name}")
        for name in ("Goal", "Inline contract context", "Steps", "Verification", "Expected result", "Out of scope"):
            if not substantive(section(body, name), 12):
                errors.append(f"{path.name} missing substantive section: {name}")
        implementation_deliverables: list[str] = []
        if require_implementation_deliverables:
            implementation_deliverables, deliverable_errors = validate_implementation_deliverables(
                path.name, body,
            )
            errors.extend(deliverable_errors)
        layer = fields.get("Layer", "").casefold()
        if layer not in {"domain", "data", "presentation", "infrastructure", "tests"}:
            errors.append(f"{path.name} must declare one allowed Layer")
        if require_boundary_owner and not substantive(fields.get("Boundary owner"), 12):
            errors.append(f"{path.name} Boundary owner must be substantive")
        try:
            task_scopes = json.loads(fields.get("Engineering scopes", ""))
        except json.JSONDecodeError:
            task_scopes = None
        if (
            not isinstance(task_scopes, list) or not task_scopes
            or not all(isinstance(item, str) and SLUG_RE.fullmatch(item) for item in task_scopes)
            or task_scopes != sorted(set(task_scopes))
        ):
            errors.append(f"{path.name} Engineering scopes must be a sorted unique non-empty JSON array")
            task_scopes = []
        status = fields.get("Status", "")
        evidence = fields.get("Evidence", "")
        if status not in {"pending", "done"}:
            errors.append(f"{path.name} Status must be pending or done")
        if status == "pending" and evidence != "none":
            errors.append(f"{path.name} pending task Evidence must be none")
        if status == "done":
            evidence_path = Path(evidence)
            target = (package / evidence_path).resolve()
            if evidence == "none" or evidence_path.is_absolute() or ".." in evidence_path.parts or not is_subpath(target, package / "evidence"):
                errors.append(f"{path.name} done task requires package evidence path")
            elif not target.is_file() or target.stat().st_size == 0:
                errors.append(f"{path.name} task evidence does not exist or is empty")
        estimate = re.fullmatch(r"([0-9.]+)\s*[–-]\s*([0-9.]+)\s*days", fields.get("Estimate (ideal)", ""))
        if not estimate or not (0 < float(estimate.group(1)) <= float(estimate.group(2)) <= 2):
            errors.append(f"{path.name} estimate must satisfy 0 < min <= max <= 2 days")
        parsed_paths, path_errors = parse_paths(fields.get("Paths", ""))
        for error in path_errors:
            errors.append(f"{path.name} {error}")
        for kind, raw in parsed_paths:
            target = (repo / raw).resolve()
            if not is_subpath(target, repo):
                errors.append(f"{path.name} path escapes repository")
            elif kind == "existing" and not target.exists():
                errors.append(f"{path.name} existing path does not exist: {raw}")
        read_only_context, context_errors = parse_read_only_context(fields.get("Read-only context", "none"))
        for error in context_errors:
            errors.append(f"{path.name} {error}")
        for raw in read_only_context:
            try:
                target = safe_repo_path(repo, raw, "Read-only context")
            except AdapterError as error:
                errors.append(f"{path.name} {error}")
                continue
            if not target.exists():
                errors.append(f"{path.name} Read-only context does not exist: {raw}")
        raw_deps = fields.get("Depends on", "")
        deps = set() if raw_deps.casefold() in {"none", "-", "—"} else set(re.findall(r"\btask-\d{3}\b", raw_deps))
        if raw_deps.casefold() not in {"none", "-", "—"} and not deps:
            errors.append(f"{path.name} invalid dependencies")
        for dep in deps - task_ids:
            errors.append(f"{path.name} depends on missing {dep}")
        if path.stem in deps:
            errors.append(f"{path.name} depends on itself")
        tasks.append({"id": path.stem, "path": path, "body": body, "layer": layer, "engineering_scopes": task_scopes, "status": status, "evidence": evidence, "deps": deps, "paths": parsed_paths, "read_only_context": read_only_context, "implementation_deliverables": implementation_deliverables})
    by_id = {str(t["id"]): t for t in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in by_id.get(node, {}).get("deps", set()):
            if visit(str(dep)):
                return True
        visiting.remove(node); visited.add(node)
        return False
    if any(visit(str(t["id"])) for t in tasks):
        errors.append("plan dependency graph contains a cycle")
    for task in tasks:
        if task["status"] == "done":
            for dep in task["deps"]:
                if by_id[str(dep)]["status"] != "done":
                    errors.append(f"{task['id']} is done before dependency {dep}")
    if validate_plan_paths:
        if adapter is None:
            errors.append("plan path validation requires platform adapter boundaries")
        else:
            production = [str(item) for item in adapter.get("production_roots", [])]
            denied = [str(item) for item in adapter.get("protected_roots", [])] + [
                str(item) for item in adapter.get("production_exclusions", [])
            ]
            writable: list[tuple[str, str, str]] = []
            contexts: list[tuple[str, str]] = []
            for task in tasks:
                task_id = str(task["id"])
                for kind, raw in task["paths"]:
                    writable.append((task_id, kind, raw))
                    try:
                        path_ownership.validate_platform_writable_path(
                            repo, adapter, raw, require_existing=kind == "existing"
                        )
                    except path_ownership.PathOwnershipError as error:
                        errors.append(f"{task_id} Paths ownership invalid: {error}")
                    target = repo / raw
                    if kind == "proposed" and target.exists():
                        errors.append(f"{task_id} proposed path already exists: {raw}")
                contexts.extend((task_id, raw) for raw in task.get("read_only_context", []))
            for index, (task_id, _kind, raw) in enumerate(writable):
                for other_task, _other_kind, other in writable[index + 1:]:
                    if paths_overlap(raw, other):
                        errors.append(
                            f"plan writable Paths overlap across {task_id}/{other_task}: {raw} <> {other}"
                        )
                for context_task, context in contexts:
                    if paths_overlap(raw, context):
                        errors.append(
                            f"writable Paths overlaps Read-only context in {task_id}/{context_task}: {raw} <> {context}"
                        )
    return tasks, errors


def state_files(repo: Path, adapter: dict[str, object], package: Path, meta: dict[str, object]) -> list[Path]:
    candidates: set[Path] = set()
    for name in ("proposal.md", "implementation-spec.md", "design.md", "verification.md", "platform-ux.md", "plan/README.md"):
        path = package / name
        if path.is_file(): candidates.add(path)
    snapshot = package / "plan/rule-selection.json"
    if snapshot.is_file(): candidates.add(snapshot)
    if (
        meta.get("change_type") == "product-backed"
        and "ui" in set(meta.get("engineering_scopes", []))
    ):
        visual_rule = repo / "workflow/rules/visual-language.md"
        if not visual_rule.is_file():
            raise AdapterError("product-backed ui terminal state requires visual-language.md")
        candidates.add(visual_rule)
    for path in (package / "plan").glob("task-*.md"):
        candidates.add(path)
    evidence_root = package / "evidence"
    if evidence_root.is_dir():
        for path in evidence_root.rglob("*"):
            if path.is_file() and path.name != "verification-state.json":
                candidates.add(path)
    for raw in meta.get("applicable_rule_files", []):
        if isinstance(raw, str):
            path = safe_repo_path(repo, raw, "applicable_rule_files")
            if path.is_file(): candidates.add(path)
    capabilities = validate_capabilities(adapter)
    if "verify" in capabilities:
        platform_root = safe_repo_path(repo, str(adapter.get("platform_root", "")), "platform_root")
        terminal_inputs = (
            repo / "workflow/rules/verification-evidence.md",
            repo / "workflow/phases/verify.md",
            platform_root / "workflow/phases/verify.md",
        )
        for path in terminal_inputs:
            if not path.is_file():
                try:
                    label = path.relative_to(repo).as_posix()
                except ValueError:
                    label = "terminal verification input"
                raise AdapterError(f"required terminal verification input is missing: {label}")
            candidates.add(path)
    shared = meta.get("shared_product_spec")
    if isinstance(shared, str):
        path = repo / shared
        if path.is_file(): candidates.add(path)
    tasks, _ = parse_tasks(repo, package)
    for task in tasks:
        for _kind, raw in task["paths"]:
            path = (repo / raw).resolve()
            if path.is_file():
                candidates.add(path)
            elif path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file() and ".git" not in child.parts:
                        candidates.add(child)
    return sorted(candidates)


def compute_state(repo: Path, adapter: dict[str, object], package: Path, meta: dict[str, object]) -> dict[str, object]:
    files: dict[str, str] = {}
    version = package_contract_version(repo, adapter, meta, package)
    projection = semantic_projection(
        repo, adapter, meta.get("engineering_scopes", []), contract_version=version
    )
    projection_bytes = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
    files["adapter/semantic-projection"] = hashlib.sha256(projection_bytes).hexdigest()
    for path in state_files(repo, adapter, package, meta):
        if is_subpath(path, package):
            key = f"package/{path.relative_to(package).as_posix()}"
        else:
            key = f"repo/{path.relative_to(repo).as_posix()}"
        files[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"fingerprint": hashlib.sha256(encoded).hexdigest(), "files": files}


def validate_state(repo: Path, adapter: dict[str, object], package: Path, meta: dict[str, object]) -> list[str]:
    raw = meta.get("verification_state")
    if not isinstance(raw, str):
        return ["verification_state must point to package evidence JSON"]
    value = Path(raw)
    path = (package / value).resolve()
    if value.is_absolute() or ".." in value.parts or not is_subpath(path, package / "evidence") or not path.is_file():
        return ["verification_state path is unsafe or missing"]
    try:
        recorded = json.loads(read(path))
    except (OSError, json.JSONDecodeError):
        return ["verification_state JSON is invalid"]
    try:
        current = compute_state(repo, adapter, package, meta)
    except (AdapterError, RuleProfileError) as error:
        return [f"verification state inputs are invalid: {error}"]
    if recorded.get("fingerprint") != current["fingerprint"] or recorded.get("files") != current["files"]:
        return ["verification state fingerprint is stale"]
    return []


def native_obligation_table(status: str = "pending") -> str:
    rows = "\n".join(
        f"| {obligation} | pending | {status} |" for obligation in NATIVE_OBLIGATION_IDS
    )
    return (
        "## Native obligation coverage\n\n"
        "| Obligation ID | Observation record | Status |\n"
        "|---|---|---|\n" + rows + "\n"
    )


def validate_native_obligations(
    package: Path, verification: str, mode: str,
) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    body = section(verification, "Native obligation coverage") or ""
    rows: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0].casefold() == "obligation id" or set(cells[0]) <= {"-", ":"}:
            continue
        rows[cells[0]].append((cells[1], cells[2]))
    expected = set(NATIVE_OBLIGATION_IDS)
    if set(rows) != expected:
        missing = sorted(expected - set(rows)); extra = sorted(set(rows) - expected)
        if missing: errors.append(f"native obligation rows missing: {', '.join(missing)}")
        if extra: errors.append(f"unknown native obligation rows: {', '.join(extra)}")
    observation_targets: set[Path] = set()
    for values in rows.values():
        for record_raw, _status_value in values:
            value = Path(record_raw)
            target = (package / value).resolve()
            if (
                record_raw != "pending" and not value.is_absolute()
                and ".." not in value.parts and is_subpath(target, package / "evidence")
            ):
                observation_targets.add(target)
    statuses: dict[str, str] = {}
    for obligation in NATIVE_OBLIGATION_IDS:
        values = rows.get(obligation, [])
        if len(values) != 1:
            if len(values) > 1: errors.append(f"native obligation row duplicate: {obligation}")
            continue
        record_raw, status_value = values[0]
        statuses[obligation] = status_value
        if mode in {"propose", "plan"} or (
            mode == "implement" and record_raw == "pending" and status_value == "pending"
        ):
            if record_raw != "pending" or status_value != "pending":
                errors.append(f"pre-verification native obligation must be pending: {obligation}")
            continue
        if status_value not in {"PASS", "FAIL", "UNKNOWN"}:
            errors.append(f"native obligation status is invalid: {obligation}")
            continue
        record_path = Path(record_raw)
        target = (package / record_path).resolve()
        if (
            record_path.is_absolute() or ".." in record_path.parts
            or not is_subpath(target, package / "evidence") or not target.is_file()
        ):
            errors.append(f"native observation record missing/unsafe: {obligation}")
            continue
        try:
            record = json.loads(read(target))
        except (OSError, json.JSONDecodeError):
            errors.append(f"native observation record JSON invalid: {obligation}")
            continue
        if not isinstance(record, dict) or set(record) != NATIVE_OBSERVATION_KEYS:
            errors.append(f"native observation record schema must be exact: {obligation}")
            continue
        if record.get("schema_version") != 1 or record.get("obligation_id") != obligation:
            errors.append(f"native observation record identity mismatch: {obligation}")
        if record.get("status") != status_value:
            errors.append(f"native row/record status mismatch: {obligation}")
        if not substantive(str(record.get("observation", "")), 12):
            errors.append(f"native observation is not substantive: {obligation}")
        else:
            errors.extend(artifact_language.validate_authored_json_string(
                record.get("observation"), f"native observation {obligation}"
            ))
        evidence_refs = record.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not all(isinstance(item, str) for item in evidence_refs):
            errors.append(f"native observation evidence_refs must be an array: {obligation}")
            evidence_refs = []
        if status_value in {"PASS", "FAIL"} and not evidence_refs:
            errors.append(f"native {status_value} requires underlying evidence refs: {obligation}")
        for raw in evidence_refs:
            value = Path(raw); evidence = (package / value).resolve()
            if (
                value.is_absolute() or ".." in value.parts
                or not is_subpath(evidence, package / "evidence")
                or evidence in observation_targets
                or not evidence.is_file() or evidence.stat().st_size == 0
            ):
                if evidence in observation_targets:
                    errors.append(f"native underlying evidence cannot reference observation record: {obligation}")
                else:
                    errors.append(f"native underlying evidence missing/unsafe: {obligation}")
        if mode in TERMINAL_MODES and status_value != "PASS":
            errors.append(f"terminal native obligation must be PASS: {obligation}")
    return statuses, errors


def affected_tasks_for_problem(
    tasks: list[dict[str, object]], task_context_ids: dict[str, set[str]], problem: str,
) -> list[dict[str, object]]:
    if problem in NATIVE_OBLIGATION_IDS:
        return [task for task in tasks if "ui" in set(task.get("engineering_scopes", []))]
    return [
        task for task in tasks
        if problem in task_context_ids.get(str(task["id"]), set())
    ]


def validate_package(repo: Path, adapter: dict[str, object], feature: str, change_id: str, mode: str) -> list[str]:
    try:
        require_capability(adapter, "archive-implementation" if mode == "archive" else mode)
    except RuleProfileError as error:
        return [str(error)]
    errors: list[str] = []
    package = changes_root(repo, adapter, feature) / change_id
    meta_path = package / "meta.json"
    if not meta_path.is_file():
        return [f"missing {meta_path.relative_to(repo)}"]
    try:
        meta = json.loads(read(meta_path))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid meta.json: {error}"]
    try:
        contract_version = package_contract_version(repo, adapter, meta, package, mode)
    except AdapterError as error:
        errors.append(str(error))
        contract_version = CURRENT_MODULARITY_CONTRACT_VERSION
    language_required = (
        contract_version == CURRENT_MODULARITY_CONTRACT_VERSION
        and any(
            ARTIFACT_LANGUAGE_RULE in rules
            for rules in adapter.get("phase_rule_profiles", {}).values()
            if isinstance(rules, list)
        )
    )
    missing_fields = REQUIRED_META - set(meta)
    if contract_version == LEGACY_MODULARITY_CONTRACT_VERSION:
        missing_fields.discard("modularity_contract_version")
    missing = sorted(missing_fields)
    if missing: errors.append(f"meta.json missing fields: {', '.join(missing)}")
    if meta.get("platform") != adapter["platform_name"]: errors.append("meta.platform does not match adapter")
    if meta.get("feature") != feature: errors.append("meta.feature does not match CLI feature")
    if meta.get("change_id") != change_id: errors.append("meta.change_id does not match CLI change")
    if meta.get("change_type") not in {"product-backed", "technical-only"}: errors.append("invalid change_type")
    if meta.get("tier") not in {"quick", "standard", "extended"}: errors.append("invalid tier")
    raw_scopes = meta.get("engineering_scopes")
    raw_rules = meta.get("applicable_rule_files")
    if not isinstance(raw_scopes, list) or not raw_scopes:
        errors.append("engineering_scopes must be a non-empty array")
    if not isinstance(raw_rules, list):
        errors.append("applicable_rule_files must be an array")
    if isinstance(raw_scopes, list) and isinstance(raw_rules, list):
        try:
            normalized_scopes, expected_rules = applicable_rules(
                repo, adapter, raw_scopes, contract_version=contract_version
            )
        except RuleProfileError as error:
            errors.append(str(error))
        else:
            if raw_scopes != normalized_scopes:
                errors.append("engineering_scopes must be sorted, unique and known")
            if raw_rules != expected_rules:
                errors.append("applicable_rule_files must exactly match lifecycle phase bases plus selected scopes")
    if mode == "propose":
        if meta.get("rule_selection_snapshot") is not None or (package / "plan/rule-selection.json").exists():
            errors.append("propose requires null rule_selection_snapshot and no planned snapshot")
    else:
        errors.extend(validate_rule_selection_snapshot(package, meta))
    if not isinstance(meta.get("blocking_questions"), list) or meta.get("blocking_questions"):
        errors.append("blocking_questions must be an empty array")
    if language_required and isinstance(meta.get("blocking_questions"), list):
        for index, value in enumerate(meta["blocking_questions"]):
            if isinstance(value, str):
                errors.extend(artifact_language.validate_authored_json_string(
                    value, f"meta.blocking_questions[{index}]"
                ))
    if not isinstance(meta.get("problems"), list):
        errors.append("problems must be an array")
    elif not all(isinstance(item, str) for item in meta.get("problems", [])):
        errors.append("problems entries must be contract ID strings")
    else:
        for value in meta.get("problems", []):
            if (
                not re.fullmatch(r"(?:REQ|AC|[A-Z][A-Z0-9]*-(?:REQ|AC))-\d+", value)
                and value not in NATIVE_OBLIGATION_IDS
            ):
                errors.append(f"problems entry is not a known contract/native obligation ID: {value}")

    shared_reqs: set[str] = set(); shared_acs: set[str] = set()
    if meta.get("change_type") == "product-backed":
        expected = f"specs/product/{feature}/spec.md"
        if meta.get("shared_product_spec") != expected:
            errors.append(f"shared_product_spec must be exactly {expected}")
        else:
            shared_path = repo / expected
            if not shared_path.is_file():
                errors.append("shared product spec missing")
            else:
                product = read(shared_path)
                if field_value(product, "Status") != "READY": errors.append("shared product spec is not READY")
                if field_value(product, "Product approval") != "APPROVED": errors.append("shared product spec is not APPROVED")
                if not valid_human(field_value(product, "Approved by")): errors.append("shared product spec has no approver")
                if not valid_human(field_value(product, "Approval evidence"), 8): errors.append("shared product spec has no approval evidence")
                shared_reqs = {x[0] for x in SHARED_REQ_RE.findall(product)}
                shared_acs = {x[0] for x in SHARED_AC_RE.findall(product)}
                errors.extend(f"product review gate: {item}" for item in validate_product_ready(repo, feature))
        if meta.get("product_status") != "READY" or meta.get("product_approval") != "APPROVED": errors.append("meta product gate must be READY/APPROVED")
        if meta.get("product_impact") != "PRESENT": errors.append("product-backed impact must be PRESENT")
    else:
        if meta.get("shared_product_spec") is not None: errors.append("technical-only shared_product_spec must be null")
        if meta.get("product_impact") != "NONE" or not substantive(str(meta.get("impact_evidence", ""))): errors.append("technical-only requires NONE impact evidence")
    impact_evidence = meta.get("impact_evidence")
    if language_required and isinstance(impact_evidence, str):
        errors.extend(artifact_language.validate_authored_json_string(
            impact_evidence, "meta.impact_evidence"
        ))

    package_scopes = set(raw_scopes) if isinstance(raw_scopes, list) else set()
    platform_ux_errors = validate_platform_ux(repo, adapter, package, feature, meta, package_scopes)
    errors.extend(platform_ux_errors)
    if platform_ux_errors and meta.get("design_gate") == "PASS":
        errors.append("design_gate cannot PASS without READY platform UX")

    required_files = ("proposal.md", "implementation-spec.md", "design.md", "verification.md")
    for name in required_files:
        if not (package / name).is_file(): errors.append(f"missing {name}")

    if language_required:
        authored_paths = [package / name for name in required_files]
        platform_ux_path = package / "platform-ux.md"
        if platform_ux_path.is_file() or platform_ux_path.is_symlink():
            authored_paths.append(platform_ux_path)
        plan_root = package / "plan"
        if mode != "propose" and plan_root.is_dir():
            plan_readme = plan_root / "README.md"
            authored_paths.append(plan_readme)
            authored_paths.extend(sorted(plan_root.glob("task-*.md")))
        for authored_path in authored_paths:
            errors.extend(validate_authored_markdown_language(repo, package, authored_path))
        for authored_path in typed_authored_report_paths(package):
            if TASK_AUTHORED_REPORT_RE.fullmatch(authored_path.name):
                errors.extend(validate_task_evidence_language(repo, package, authored_path))
            else:
                errors.extend(validate_authored_markdown_language(repo, package, authored_path))
    if any(not (package / name).is_file() for name in required_files): return errors

    proposal = read(package / "proposal.md")
    for heading in ("Intake", "Goal", "Scope", "Engineering scope selection", "Applicable rule files", "Non-goals", "Accepted decisions", "Risks"):
        if not substantive(section(proposal, heading), 16): errors.append(f"proposal.md missing substantive section: {heading}")
    if not explicit_none(section(proposal, "Open questions")): errors.append("proposal.md has unresolved questions")

    spec = read(package / "implementation-spec.md")
    for heading in ("Intake reference", "Shared contract references", "Platform requirements", "Platform acceptance criteria", "Constraints", "Integration points"):
        if not substantive(section(spec, heading), 12): errors.append(f"implementation-spec.md missing substantive section: {heading}")
    if not explicit_none(section(spec, "Open questions")): errors.append("implementation-spec.md has unresolved questions")
    if SHARED_COPY_RE.search(spec): errors.append("shared REQ/AC declaration duplicated")
    prefix = str(adapter["contract_prefix"])
    req_blocks = heading_blocks(spec, re.compile(rf"(?m)^###\s+({prefix}-REQ-\d+)\s+[—-]\s+.+$"))
    ac_blocks = heading_blocks(spec, re.compile(rf"(?m)^###\s+({prefix}-AC-\d+)\s+[—-]\s+.+$"))
    req_ids = [x[0] for x in req_blocks]; ac_ids = [x[0] for x in ac_blocks]
    declared_reqs = set(req_ids); declared_acs = set(ac_ids)
    if not req_ids or len(req_ids) != len(declared_reqs): errors.append("platform requirement IDs missing or duplicate")
    if not ac_ids or len(ac_ids) != len(declared_acs): errors.append("platform AC IDs missing or duplicate")
    covered: set[str] = set()
    for req, body in req_blocks:
        if not substantive(body, 16): errors.append(f"{req} has no substantive contract")
    for ac, body in ac_blocks:
        covers = re.search(r"(?mi)^`?Covers\s*:\s*([^`\n]+)`?\s*$", body)
        refs = set(re.findall(rf"\b{prefix}-REQ-\d+\b", covers.group(1))) if covers else set()
        if not refs: errors.append(f"{ac} has no Covers")
        if refs - declared_reqs: errors.append(f"{ac} covers undeclared requirement")
        covered |= refs & declared_reqs
    if declared_reqs - covered: errors.append("platform requirements lack AC coverage")

    design = read(package / "design.md")
    if meta.get("tier") == "quick" and re.search(r"(?mi)^Design status:\s*NOT_APPLICABLE:\s*(.+)$", design):
        reason = re.search(r"(?mi)^Design status:\s*NOT_APPLICABLE:\s*(.+)$", design).group(1)
        if not substantive(reason, 16): errors.append("quick design N/A reason is not substantive")
    else:
        for heading in COMMON_DESIGN:
            if not substantive(section(design, heading), 28): errors.append(f"design.md missing substantive section: {heading}")
        if meta.get("tier") == "extended":
            for heading in adapter["extended_design_sections"]:
                if not substantive(section(design, str(heading)), 28): errors.append(f"extended design missing: {heading}")
    if contract_version == CURRENT_MODULARITY_CONTRACT_VERSION:
        errors.extend(validate_modularity_decision(repo, adapter, design, package_scopes))
    scope_section = section(design, "Applied engineering scopes") or ""
    scope_entries: dict[str, str] = {}
    duplicate_scopes: set[str] = set()
    for match in re.finditer(r"(?m)^-\s*([a-z0-9]+(?:-[a-z0-9]+)*):\s*(.+)$", scope_section):
        scope = match.group(1); rationale = match.group(2).strip()
        if scope in scope_entries:
            duplicate_scopes.add(scope)
        scope_entries[scope] = rationale
        if not substantive(rationale, 12):
            errors.append(f"design scope has no decision or explicit N/A rationale: {scope}")
    if duplicate_scopes:
        errors.append(f"design engineering scopes duplicate: {', '.join(sorted(duplicate_scopes))}")
    expected_scope_set = set(raw_scopes) if isinstance(raw_scopes, list) else set()
    if set(scope_entries) != expected_scope_set:
        errors.append("design Applied engineering scopes must exactly cover meta engineering_scopes")
    if meta.get("design_gate") != "PASS": errors.append("design_gate must be PASS")
    if meta.get("change_type") == "product-backed" and "ui" in package_scopes:
        if not substantive(section(design, "Platform UX trace and decisions"), 28):
            errors.append("design.md must incorporate Platform UX trace and decisions")

    verification = read(package / "verification.md")
    if contract_version == CURRENT_MODULARITY_CONTRACT_VERSION:
        errors.extend(validate_modularity_verification(verification, mode))
    native_required = (
        contract_version == CURRENT_MODULARITY_CONTRACT_VERSION
        and meta.get("change_type") == "product-backed"
        and "ui" in package_scopes
    )
    native_status: dict[str, str] = {}
    if native_required:
        if not substantive(section(verification, "Native UX verification"), 20):
            errors.append("verification.md requires Native UX verification")
        native_status, native_errors = validate_native_obligations(package, verification, mode)
        errors.extend(native_errors)
    rows: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for line in verification.splitlines():
        if not line.lstrip().startswith("|"): continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].casefold() in {"contract id", "---"} or set(cells[0]) <= {"-", ":"}: continue
        rows[cells[0]].append((cells[2], cells[3], cells[4]))
    for contract in shared_reqs | shared_acs | declared_reqs | declared_acs:
        if len(rows.get(contract, [])) != 1: errors.append(f"verification row missing or duplicate: {contract}")
    def concrete_evidence(contract: str, evidence: str) -> bool:
        value = Path(evidence); target = (package / value).resolve()
        valid = (
            not value.is_absolute() and ".." not in value.parts
            and is_subpath(target, package / "evidence")
            and target.is_file() and target.stat().st_size > 0
        )
        if not valid:
            errors.append(f"verification evidence missing/unsafe: {contract}")
        return valid

    row_status: dict[str, str] = {}
    for contract, values in rows.items():
        for method, evidence, status in values:
            row_status[contract] = status
            if not substantive(method, 4): errors.append(f"verification method empty: {contract}")
            if mode in TERMINAL_MODES:
                if status != "PASS": errors.append(f"verification status must be exact PASS: {contract}")
                concrete_evidence(contract, evidence)
            elif mode == "implement" and status in {"PASS", "FAIL", "UNKNOWN"}:
                concrete_evidence(contract, evidence)
            elif status.lower() != "pending":
                errors.append(f"pre-verification row has invalid status: {contract}")
    all_verification_status = dict(row_status)
    all_verification_status.update(native_status)

    if mode == "propose":
        if meta.get("problems") != []: errors.append("propose requires empty problems")
        if any(status.casefold() != "pending" for status in all_verification_status.values()): errors.append("propose verification rows must be pending")
        if meta.get("status") != "specified": errors.append("propose requires specified status")
        if meta.get("tasks_total") != 0 or meta.get("tasks_done") != 0: errors.append("specified package task counts must be zero")
        if meta.get("verification_status") != "pending" or meta.get("verified_at") is not None or meta.get("verification_state") is not None: errors.append("specified verification fields must be pending/null")
        return errors

    tasks, task_errors = parse_tasks(
        repo, package,
        require_boundary_owner=contract_version == CURRENT_MODULARITY_CONTRACT_VERSION,
        adapter=adapter,
        validate_plan_paths=mode == "plan" and contract_version == CURRENT_MODULARITY_CONTRACT_VERSION,
        require_implementation_deliverables=contract_version == CURRENT_MODULARITY_CONTRACT_VERSION,
    ); errors.extend(task_errors)
    readme = package / "plan" / "README.md"
    if not readme.is_file(): errors.append("plan/README.md missing")
    else:
        index = read(readme)
        for heading in ("Planning frame", "DAG", "Estimates and multipliers", "Verification strategy"):
            if not substantive(section(index, heading), 16): errors.append(f"plan README missing substantive section: {heading}")
        for task in tasks:
            if str(task["id"]) not in (section(index, "DAG") or ""): errors.append(f"plan DAG omits {task['id']}")
    done = sum(t["status"] == "done" for t in tasks)
    if not tasks or meta.get("tasks_total") != len(tasks): errors.append("tasks_total must equal non-zero derived task count")
    if meta.get("tasks_done") != done: errors.append("tasks_done must equal derived done task count")
    known_reqs = shared_reqs | declared_reqs; known_acs = shared_acs | declared_acs; known = known_reqs | known_acs
    task_context_ids: dict[str, set[str]] = {}
    covered_task_scopes: set[str] = set()
    for task in tasks:
        context = section(str(task["body"]), "Inline contract context") or ""
        ids = set(re.findall(r"\b(?:REQ|AC|[A-Z][A-Z0-9]*-(?:REQ|AC))-\d+\b", context))
        task_context_ids[str(task["id"])] = ids
        if not ids & known_reqs or not ids & known_acs: errors.append(f"{task['id']} inline context lacks declared REQ/AC")
        if ids - known: errors.append(f"{task['id']} inline context contains unknown IDs")
        task_scopes = set(str(item) for item in task.get("engineering_scopes", []))
        covered_task_scopes.update(task_scopes)
        package_scopes = set(raw_scopes) if isinstance(raw_scopes, list) else set()
        if task_scopes - package_scopes:
            errors.append(f"{task['id']} contains scope not sealed in package")
        for scope in sorted(task_scopes):
            missing_dependencies = set(adapter.get("scope_dependencies", {}).get(scope, [])) - task_scopes
            if missing_dependencies:
                errors.append(
                    f"{task['id']} scope {scope} requires task scopes: {', '.join(sorted(missing_dependencies))}"
                )
        if task["layer"] == "presentation" and "ui" not in task_scopes:
            errors.append(f"{task['id']} presentation task must include ui engineering scope")
        task_check_text = "\n".join(
            section(str(task["body"]), heading) or ""
            for heading in ("Steps", "Verification", "Expected result")
        ).casefold()
        for scope in sorted(task_scopes):
            for check in scope_task_checks_for_version(adapter, scope, contract_version):
                if str(check).casefold() not in task_check_text:
                    errors.append(f"{task['id']} missing {scope} scope check: {check}")
        if meta.get("change_type") == "product-backed" and "ui" in task_scopes:
            for check in adapter["platform_ux"]["task_checks"]:
                if str(check).casefold() not in task_check_text:
                    errors.append(f"{task['id']} missing native UX check: {check}")
    if package_scopes - covered_task_scopes:
        errors.append(f"plan tasks do not cover engineering scopes: {', '.join(sorted(package_scopes - covered_task_scopes))}")

    if mode == "plan":
        if meta.get("problems") != []: errors.append("plan requires empty problems")
        if any(status.casefold() != "pending" for status in all_verification_status.values()): errors.append("plan verification rows must be pending")
        if meta.get("status") != "planned": errors.append("plan requires planned status")
        if done: errors.append("new plan tasks must all be pending")
        if meta.get("verification_status") != "pending": errors.append("plan verification must be pending")
    elif mode == "implement":
        if meta.get("status") not in {"planned", "implementing"}: errors.append("implement requires planned or implementing status")
        verification_status = meta.get("verification_status")
        problems = [item for item in meta.get("problems", []) if isinstance(item, str)] if isinstance(meta.get("problems"), list) else []
        if verification_status == "pending":
            if problems: errors.append("initial implement state requires empty problems")
            if any(status.casefold() != "pending" for status in all_verification_status.values()): errors.append("initial implement verification rows must be pending")
            if meta.get("verified_at") is not None or meta.get("verification_state") is not None: errors.append("initial implement verification timestamp/state must be null")
        elif verification_status in {"FAIL", "UNKNOWN"}:
            if meta.get("status") != "implementing": errors.append("recovery state requires implementing status")
            if meta.get("verified_at") is not None or meta.get("verification_state") is not None: errors.append("recovery verified_at/state must be null")
            if any(status not in {"PASS", "FAIL", "UNKNOWN"} for status in all_verification_status.values()): errors.append("recovery rows must be exact PASS/FAIL/UNKNOWN")
            non_pass = {contract for contract, status in all_verification_status.items() if status in {"FAIL", "UNKNOWN"}}
            if not non_pass: errors.append("recovery state requires at least one FAIL/UNKNOWN row")
            expected_status = "FAIL" if any(all_verification_status.get(contract) == "FAIL" for contract in non_pass) else "UNKNOWN"
            if verification_status != expected_status: errors.append("recovery verification_status does not match row precedence")
            if set(problems) != non_pass or len(problems) != len(non_pass): errors.append("recovery problems must exactly equal non-PASS contract IDs")
            direct_affected: set[str] = set()
            for contract in non_pass:
                mapped = affected_tasks_for_problem(tasks, task_context_ids, contract)
                if not mapped:
                    errors.append(f"recovery problem has no task mapping; repair plan: {contract}")
                direct_affected.update(str(task["id"]) for task in mapped)
            closure = set(direct_affected)
            changed = True
            while changed:
                changed = False
                for task in tasks:
                    task_id = str(task["id"])
                    if task_id not in closure and set(task["deps"]) & closure:
                        closure.add(task_id); changed = True
            by_task_id = {str(task["id"]): task for task in tasks}
            for task_id in sorted(closure):
                task = by_task_id[task_id]
                if task["status"] != "pending" or task["evidence"] != "none":
                    errors.append(f"recovery closure task must be pending with Evidence none: {task_id}")
        else:
            errors.append("implement verification_status must be pending, FAIL or UNKNOWN")
    else:
        if meta.get("problems") != []: errors.append(f"{mode} requires empty problems")
        if meta.get("status") != "verified": errors.append(f"{mode} requires verified status")
        if done != len(tasks): errors.append(f"{mode} requires all tasks done")
        if meta.get("verification_status") != "PASS": errors.append("terminal verification_status must be PASS")
        if not valid_human(str(meta.get("verified_at", "")), 8): errors.append("verified_at is missing")
        errors.extend(validate_state(repo, adapter, package, meta))
    return errors


def fixture_platform_ux(adapter: dict[str, object], feature: str = "sample") -> str:
    config = adapter["platform_ux"]
    sections = []
    evidence = "Repository SDK, dependency, deployment and existing component evidence was inspected."
    for heading in PLATFORM_UX_HEADINGS[:-1]:
        sections.append(f"## {heading}\n\n{evidence} Native behavior maps the shared intent with accessible fallbacks.\n")
    terms = "; ".join(str(item) for item in config["required_terms"])
    return (
        f"# {feature} native UX\n\n"
        "- **UX status:** `READY`\n"
        f"- **Platform:** `{adapter['platform_name']}`\n"
        f"- **Source product UX:** `specs/product/{feature}/ux.md`\n"
        f"- **Native design language adapter:** `{config['design_language']}`\n"
        "- **Color direction:** `soft blue`\n\n"
        + "\n".join(sections)
        + f"\nNative terms: {terms}.\n\n## Open gaps\n\nNone.\n"
    )


def fixture_modularity_decision(outcome: str = "not-applicable") -> str:
    if outcome == "isolated":
        triggers = "independent-feature=yes; domain-data=yes; network=no; persistence=no; reusable-ui=no; consumers=2; independent-ownership=yes"
        physical = "A proposed Test library package owns the cohesive capability behind a minimal public contract."
        evidence = "TestClient/workflow/package.md; TestClient/workflow/platform-contract.json"
        rationale = "Independent ownership and focused testability justify a physical package boundary with minimal API overhead."
        migration = "The boundary exists now; revisit API/implementation split when a second implementation or consumer is approved."
        overmod = "One cohesive capability stays in one unit; no package is created per folder, class or horizontal layer."
    elif outcome == "deviation":
        triggers = "independent-feature=yes; domain-data=yes; network=yes; persistence=yes; reusable-ui=no; consumers=2; independent-ownership=yes"
        physical = "An existing Test library package combines the related capabilities behind one typed public contract."
        evidence = "TestClient/workflow/package.md; TestClient/workflow/platform-contract.json"
        rationale = "The temporary constraint outweighs extraction now while preserving ownership and a reviewable dependency seam."
        migration = "A typed SampleCapability protocol is the migration boundary; extract after the legacy build constraint is removed."
        overmod = "The temporary local placement avoids speculative API/implementation units while retaining one cohesive owner."
    else:
        triggers = "independent-feature=no; domain-data=no; network=no; persistence=no; reusable-ui=no; consumers=1; independent-ownership=no"
        physical = "The tiny local behavior remains within its existing cohesive owner; no new physical unit is proposed."
        evidence = "TestClient/workflow/base.md; TestClient/workflow/platform-contract.json"
        rationale = "A physical split adds build and API overhead without ownership, visibility, reuse or testability benefit."
        migration = "The typed local seam is retained; reconsider isolation when a second consumer or independent owner appears."
        overmod = "A unit-per-layer split would fragment one tiny cohesive behavior and add boundaries without measurable benefit."
    return (
        "## Modularity decision\n\n"
        f"- Outcome: {outcome}\n"
        f"- Capability triggers: {triggers}\n"
        f"- Physical boundaries: {physical}\n"
        "- Public contracts and dependency direction: A typed SampleCapability contract keeps the consumer directed toward the boundary.\n"
        f"- App-shell responsibilities: {APP_SHELL_RESPONSIBILITIES}\n"
        "- App-shell capability ownership: none\n"
        f"- Repository evidence: {evidence}\n"
        f"- Rationale and trade-offs: {rationale}\n"
        f"- Migration boundary and trigger: {migration}\n"
        f"- Over-modularization check: {overmod}\n"
        "- Boundary guard verdict: PASS\n"
    )


def fixture_modularity_verification(status: str = "pending") -> str:
    return (
        "## Modularity verification\n\n"
        f"- Dependency graph: {status}\n"
        f"- Public API and visibility: {status}\n"
        f"- Module-level tests: {status}\n"
        f"- Consumer integration and build: {status}\n"
        f"- App-shell allowlist: {status}\n"
    )


def write_fixture_legacy_registry(
    repo: Path, package: Path, meta: dict[str, object]
) -> None:
    path = repo / LEGACY_REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
                "schema_version": 1,
                "task_normalization": {"ignored_field_values": ["Status", "Evidence"]},
                "packages": [
                    {
                        "platform": meta["platform"],
                        "feature": meta["feature"],
                        "change_id": meta["change_id"],
                        "package_path": package.relative_to(repo).as_posix(),
                        "hashes": legacy_package_hashes(package, meta),
                    }
                ],
            }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Synthetic repositories use an explicit in-process pin; production always
    # uses the tracked code constants above.
    rule_profiles.LEGACY_REGISTRY_CANONICAL_SHA256 = rule_profiles._canonical_hash(payload)
    rule_profiles.LEGACY_REGISTRY_IDENTITIES = (
        (
            str(meta["platform"]), str(meta["feature"]), str(meta["change_id"]),
            package.relative_to(repo).as_posix(),
        ),
    )


def adapter_modularity_decision(
    adapter: dict[str, object], outcome: str, evidence: str, physical: str,
    triggers: str,
) -> str:
    return (
        "# Design\n\n## Modularity decision\n\n"
        f"- Outcome: {outcome}\n"
        f"- Capability triggers: {triggers}\n"
        f"- Physical boundaries: {physical}\n"
        "- Public contracts and dependency direction: A typed Capability contract keeps consumers dependent on the public API and preserves an acyclic graph.\n"
        f"- App-shell responsibilities: {APP_SHELL_RESPONSIBILITIES}\n"
        "- App-shell capability ownership: none\n"
        f"- Repository evidence: {evidence}\n"
        "- Rationale and trade-offs: The selected boundary balances cohesive ownership, visibility, consumer independence and build overhead.\n"
        "- Migration boundary and trigger: The typed Capability contract is the seam; reconsider after a second implementation or ownership split is approved.\n"
        "- Over-modularization check: One cohesive capability uses one physical unit and avoids class-by-class fragmentation.\n"
        "- Boundary guard verdict: PASS\n"
    )


def write_fixture(repo: Path) -> tuple[dict[str, object], Path, dict[str, object]]:
    adapter_dir = repo / "TestClient" / "workflow"; adapter_dir.mkdir(parents=True)
    adapter = {
        "platform_input": "test-client", "platform_name": "TestClient", "platform_root": "TestClient",
        "lifecycle_capabilities": ["propose", "plan", "implement", "verify", "archive-implementation"],
        "package_root": "TestClient/specs", "active_changes_namespace": "changes", "archive_namespace": "archive",
        "production_roots": ["TestClient"], "protected_roots": ["TestClient/specs", "TestClient/workflow"],
        "production_exclusions": ["TestClient/specs", "TestClient/workflow"], "contract_prefix": "TST",
        "boundary_guard": "test-boundary", "extended_design_sections": ["System-design review"],
        "ui_task_checks": ["simulator", "accessibility", "design-system"],
        "platform_ux": {
            "role": "test-ux-designer", "artifact": "platform-ux.md",
            "design_language": "Native Test UI",
            "required_terms": ["Native Test UI", "soft blue", "light", "dark", "fallback", "native-term-marker"],
            "task_checks": ["platform-ux.md", "Native Test UI", "light/dark", "fallback"],
        },
        "modularity": {
            "contract_version": 1,
            "isolation_scope": "package",
            "platform_rule": "TestClient/workflow/package.md",
            "physical_units": ["Test library package", "Test non-application target"],
            "legacy_task_checks": ["package consumer", "package build"],
        },
        "rule_files": [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/performance-a.md", "TestClient/workflow/performance-b.md",
            "TestClient/workflow/ui.md", "TestClient/workflow/localization.md",
            "TestClient/workflow/package.md", "TestClient/workflow/networking.md",
            "TestClient/workflow/startup.md",
        ],
        "phase_rule_profiles": {
            "propose": ["TestClient/workflow/base.md"],
            "plan": ["TestClient/workflow/base.md"],
            "implement": ["TestClient/workflow/base.md"],
            "verify": ["TestClient/workflow/base.md"],
        },
        "scope_rule_profiles": {
            "application": ["TestClient/workflow/application.md"],
            "performance": ["TestClient/workflow/performance-a.md", "TestClient/workflow/performance-b.md"],
            "ui": ["TestClient/workflow/ui.md"],
            "localization": ["TestClient/workflow/localization.md"],
            "package": ["TestClient/workflow/package.md"],
            "networking": ["TestClient/workflow/networking.md"],
            "startup": ["TestClient/workflow/startup.md"],
        },
        "scope_task_checks": {
            "ui": ["simulator", "accessibility", "design-system"],
            "localization": ["localization"],
            "package": ["package consumer", "package build"],
            "networking": ["cache policy", "retry policy"],
            "performance": ["performance budget"],
            "startup": ["launch budget"],
        },
        "context_file_suffixes": [".md", ".json", ".swift"],
        "context_excluded_directories": [".build"],
        "context_always_include_globs": ["TestClient/**/Package.swift"],
        "pre_commit": {
            "source_suffixes": [".swift"],
            "generated_globs": ["TestClient/**/build/**"],
            "secret_globs": ["TestClient/**/*.key"],
            "security_sensitive_globs": ["TestClient/**/Config.json"],
            "ui_globs": ["TestClient/**/*View.swift"],
            "localization_globs": ["TestClient/**/*.strings"],
            "project_globs": ["TestClient/**/Package.swift"],
            "tool_globs": {"build-tool": ["TestClient/**/Package.swift"]},
        },
    }
    (adapter_dir / "platform-contract.json").write_text(json.dumps(adapter), encoding="utf-8")
    (adapter_dir / "base.md").write_text("Current lifecycle base rule.\n", encoding="utf-8")
    (adapter_dir / "application.md").write_text("Current selected application rule.\n", encoding="utf-8")
    (adapter_dir / "performance-a.md").write_text("Unselected performance rule A.\n", encoding="utf-8")
    (adapter_dir / "performance-b.md").write_text("Unselected performance rule B.\n", encoding="utf-8")
    (adapter_dir / "ui.md").write_text("Unselected UI rule.\n", encoding="utf-8")
    (adapter_dir / "localization.md").write_text("Unselected localization rule.\n", encoding="utf-8")
    (adapter_dir / "package.md").write_text("Unselected package rule.\n", encoding="utf-8")
    (adapter_dir / "networking.md").write_text("Unselected networking rule.\n", encoding="utf-8")
    (adapter_dir / "startup.md").write_text("Unselected startup rule.\n", encoding="utf-8")
    platform_verify = adapter_dir / "phases/verify.md"; platform_verify.parent.mkdir(parents=True)
    platform_verify.write_text("Current platform verification addendum.\n", encoding="utf-8")
    common_rule = repo / "workflow/rules/verification-evidence.md"; common_rule.parent.mkdir(parents=True)
    common_rule.write_text("Current universal terminal verification evidence policy.\n", encoding="utf-8")
    (common_rule.parent / "visual-language.md").write_text(
        "Current shared calm soft-blue semantic visual language contract.\n", encoding="utf-8"
    )
    common_phase = repo / "workflow/phases/verify.md"; common_phase.parent.mkdir(parents=True)
    common_phase.write_text("Current universal terminal verification phase.\n", encoding="utf-8")
    product_validator = load_product_validator()
    product = repo / "specs/product/sample/spec.md"; product.parent.mkdir(parents=True)
    (product.parent / "brief.md").write_text("Содержательный общий продуктовый brief для fixture.\n", encoding="utf-8")
    (product.parent / "ux.md").write_text("Общий спокойный soft-blue UX замысел для обоих клиентов.\n", encoding="utf-8")
    product.write_text(product_validator.fixture_spec(), encoding="utf-8")
    product_validator.write_fixture_receipt(repo, "sample")
    product.write_text(product.read_text(encoding="utf-8").replace("`DRAFT`", "`READY`", 1), encoding="utf-8")
    fixture_product_errors = product_validator.check_product(repo, "sample")
    if fixture_product_errors:
        raise AssertionError(fixture_product_errors)
    package = repo / "TestClient/specs/sample/changes/sample"; package.mkdir(parents=True)
    meta = {"platform":"TestClient","feature":"sample","change_id":"sample","change_type":"product-backed","tier":"standard","status":"specified","shared_product_spec":"specs/product/sample/spec.md","product_status":"READY","product_approval":"APPROVED","product_impact":"PRESENT","impact_evidence":"одобренное общее поведение применимо","engineering_scopes":["application"],"applicable_rule_files":["TestClient/workflow/base.md","TestClient/workflow/application.md"],"rule_selection_snapshot":None,"modularity_contract_version":1,"blocking_questions":[],"problems":[],"design_gate":"PASS","tasks_total":0,"tasks_done":0,"verification_status":"pending","verified_at":None,"verification_state":None}
    (package/"meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (package/"proposal.md").write_text("# Proposal\n\n## Intake\nApproved shared product contract is the implementation intake.\n\n## Goal\nDeliver the selected behavior within the platform boundary.\n\n## Scope\nTyped platform implementation and focused verification are included.\n\n## Engineering scope selection\nApplication scope is selected from discovered production ownership.\n\n## Applicable rule files\nExact lifecycle union includes the base and selected application rules.\n\n## Non-goals\nOther platforms and unrelated cleanup remain outside this change.\n\n## Accepted decisions\nUse adapter ownership and preserve the approved shared behavior.\n\n## Open questions\nNone.\n\n## Risks\nGreenfield integration requires focused boundary verification.\n", encoding="utf-8")
    (package/"implementation-spec.md").write_text("# Spec\n\n## Intake reference\nApproved shared contract applies to this platform change.\n\n## Shared contract references\nReferences REQ-1 and AC-1 without copying behavior text.\n\n## Platform requirements\n### TST-REQ-1 — Boundary\nA typed boundary isolates platform integration and supports focused verification.\n\n## Platform acceptance criteria\n### TST-AC-1 — Boundary result\nA focused test observes the typed boundary returning a deterministic result.\nCovers: TST-REQ-1\n\n## Constraints\nPreserve shared behavior and adapter ownership boundaries.\n\n## Integration points\nConnect through the discovered platform composition boundary.\n\n## Open questions\nNone.\n", encoding="utf-8")
    (package/"design.md").write_text(
        "# Design\n\n## Current context\nThe platform change is greenfield and uses only discovered integration boundaries.\n\n"
        "## Proposed architecture and boundaries\nA typed feature boundary separates domain behavior from platform integration details.\n\n"
        "## Data and control flow\nInput crosses the domain boundary and a typed result returns to the caller.\n\n"
        "## Error and recovery model\nExplicit errors preserve deterministic recovery and prevent hidden retry behavior.\n\n"
        + fixture_modularity_decision()
        + "\n## Applied engineering scopes\n- application: Typed application boundaries and deterministic tests apply to this change.\n\n"
        "## Verification strategy\nFocused tests verify the domain boundary and current realized integration path.\n",
        encoding="utf-8",
    )
    (package/"verification.md").write_text(
        "# Verification\n\n" + fixture_modularity_verification()
        + "\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | approval record | pending |\n| AC-1 | integration | Run shared scenario | scenario report | pending |\n| TST-REQ-1 | design | Review current boundary | review record | pending |\n| TST-AC-1 | unit | Run focused boundary test | test report | pending |\n",
        encoding="utf-8",
    )
    return load_adapter(repo, "test-client"), package, meta


def self_test() -> int:
    real_adapters: list[dict[str, object]] = []
    for platform in ("ios", "android"):
        real_adapter = load_adapter(repository_root(), platform)
        real_adapters.append(real_adapter)
        config = real_adapter["modularity"]
        assert config["isolation_scope"] in real_adapter["scope_rule_profiles"]
        assert config["physical_units"], f"{platform} modularity physical units missing"
        assert ARTIFACT_LANGUAGE_RULE in real_adapter["rule_files"]
        assert all(
            ARTIFACT_LANGUAGE_RULE in real_adapter["phase_rule_profiles"][phase]
            for phase in ("propose", "plan", "implement", "verify")
        )
        legacy_errors = validate_package(
            repository_root(), real_adapter,
            "client-bootstrap", "initial-scaffold", "implement",
        )
        assert legacy_errors == [], (
            f"{platform} registry-anchored v0 implement regression",
            legacy_errors,
        )
    for real_adapter in real_adapters:
        with tempfile.TemporaryDirectory() as adapter_tmp:
            synthetic_repo = Path(adapter_tmp).resolve()
            platform_root = str(real_adapter["platform_root"])
            package = synthetic_repo / platform_root / "specs/sample/changes/sample"
            plan = package / "plan"; plan.mkdir(parents=True)
            context_ref = f"{platform_root}/specs/context.md"
            context_path = synthetic_repo / context_ref; context_path.parent.mkdir(parents=True, exist_ok=True)
            context_path.write_text("Контекст только для чтения.\n", encoding="utf-8")
            source_suffix = ".swift" if str(real_adapter["platform_input"]) == "ios" else ".kt"
            writable_ref = f"{platform_root}/Synthetic/Feature{source_suffix}"
            deliverables_block = (
                "## Implementation deliverables\n"
                "- Типизированная граница поведения в production файле.\n"
                "- Focused test для наблюдаемого результата границы.\n\n"
            )
            synthetic_task = (
                "# task-001\n- Layer: domain\n- Boundary owner: Synthetic capability boundary\n"
                "- Engineering scopes: [\"application\"]\n- Depends on: none\n"
                "- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n"
                f"- Read-only context: [\"{context_ref}\"]\n- Paths: proposed: {writable_ref}\n\n"
                "## Goal\nСоздать синтетическую границу.\n\n## Inline contract context\n"
                "REQ-1 и AC-1 задают наблюдаемую границу.\n\n" + deliverables_block +
                "## Steps\nСоздать production файл.\n\n"
                "## Verification\nПроверить focused сценарий.\n\n## Expected result\n"
                "Сценарий подтверждает результат.\n\n## Out of scope\nОстальные изменения исключены.\n"
            )
            task_path = plan / "task-001.md"; task_path.write_text(synthetic_task, encoding="utf-8")
            _tasks, real_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter, validate_plan_paths=True,
                require_implementation_deliverables=True,
            )
            assert real_errors == [], (real_adapter["platform_input"], real_errors)
            russian_outcomes = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Пользователь увидит сохранённый выбор после повторного открытия.\n"
                "2. Возврат на экран восстанавливает выбранную вкладку навигации.\n\n",
                1,
            )
            task_path.write_text(russian_outcomes, encoding="utf-8")
            _tasks, russian_outcome_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert russian_outcome_errors == [], (
                real_adapter["platform_input"], russian_outcome_errors,
            )
            russian_hyphenated = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Северо-западный маршрут сохраняет выбранную вкладку навигации.\n"
                "2. Повторное открытие восстанавливает выбранное состояние экрана.\n\n",
                1,
            )
            task_path.write_text(russian_hyphenated, encoding="utf-8")
            _tasks, russian_hyphenated_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert russian_hyphenated_errors == [], (
                real_adapter["platform_input"], russian_hyphenated_errors,
            )
            separate_technical_terms = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- SwiftUI отображает сохранённое состояние выбранной вкладки навигации.\n"
                "2. Material восстанавливает понятный маршрут после повторного открытия.\n\n",
                1,
            )
            task_path.write_text(separate_technical_terms, encoding="utf-8")
            _tasks, separate_technical_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert separate_technical_errors == [], (
                real_adapter["platform_input"], separate_technical_errors,
            )
            missing_deliverables = synthetic_task.replace(deliverables_block, "", 1)
            task_path.write_text(missing_deliverables, encoding="utf-8")
            _tasks, missing_deliverable_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("missing section: Implementation deliverables" in error for error in missing_deliverable_errors), (
                real_adapter["platform_input"], missing_deliverable_errors,
            )
            fenced_only = missing_deliverables.replace(
                "## Steps\n",
                "```markdown\n## Implementation deliverables\n"
                "- Fake boundary artifact inside code.\n"
                "- Fake focused test inside code.\n```\n\n## Steps\n",
                1,
            )
            task_path.write_text(fenced_only, encoding="utf-8")
            _tasks, fenced_only_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("missing section: Implementation deliverables" in error for error in fenced_only_errors), (
                real_adapter["platform_input"], fenced_only_errors,
            )
            quoted_only = missing_deliverables.replace(
                "## Steps\n",
                "> ## Implementation deliverables\n"
                "> - Quoted boundary artifact.\n"
                "> - Quoted focused test.\n\n## Steps\n",
                1,
            )
            task_path.write_text(quoted_only, encoding="utf-8")
            _tasks, quoted_only_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("missing section: Implementation deliverables" in error for error in quoted_only_errors), (
                real_adapter["platform_input"], quoted_only_errors,
            )
            nested_first = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "  - Вложенное описание навигационного перехода.\n"
                "- Пользователь увидит сохранённый выбор после возврата.\n\n",
                1,
            )
            task_path.write_text(nested_first, encoding="utf-8")
            _tasks, nested_first_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("at least two top-level" in error for error in nested_first_errors), (
                real_adapter["platform_input"], nested_first_errors,
            )
            fenced_literal_heading = synthetic_task.replace(
                deliverables_block,
                deliverables_block.replace(
                    "\n\n", "\n```markdown\n## Implementation deliverables\n- Literal heading in code.\n```\n\n", 1,
                ),
                1,
            )
            task_path.write_text(fenced_literal_heading, encoding="utf-8")
            _tasks, fenced_literal_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert fenced_literal_errors == [], (
                real_adapter["platform_input"], fenced_literal_errors,
            )
            misplaced_deliverables = synthetic_task.replace(deliverables_block, "", 1).replace(
                "## Verification\n", deliverables_block + "## Verification\n", 1,
            )
            task_path.write_text(misplaced_deliverables, encoding="utf-8")
            _tasks, misplaced_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("must be between" in error for error in misplaced_errors), (
                real_adapter["platform_input"], misplaced_errors,
            )
            duplicate_deliverables = synthetic_task.replace(
                "## Steps\n", deliverables_block + "## Steps\n", 1,
            )
            task_path.write_text(duplicate_deliverables, encoding="utf-8")
            _tasks, duplicate_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("appear exactly once" in error for error in duplicate_errors), (
                real_adapter["platform_input"], duplicate_errors,
            )
            prose_only = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\nБудет создана граница и проверено её поведение.\n\n",
                1,
            )
            task_path.write_text(prose_only, encoding="utf-8")
            _tasks, prose_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("at least two top-level" in error for error in prose_errors), (
                real_adapter["platform_input"], prose_errors,
            )
            one_item = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n- Типизированная граница поведения в production файле.\n\n",
                1,
            )
            task_path.write_text(one_item, encoding="utf-8")
            _tasks, one_item_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("at least two top-level" in error for error in one_item_errors), (
                real_adapter["platform_input"], one_item_errors,
            )
            generic_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Реализовать необходимую задачу.\n"
                "- Выполнить требуемую работу.\n\n",
                1,
            )
            task_path.write_text(generic_items, encoding="utf-8")
            _tasks, generic_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("Implementation deliverables item" in error for error in generic_errors) == 2, (
                real_adapter["platform_input"], generic_errors,
            )
            generic_project_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Создать необходимые изменения в проекте.\n"
                "- Добавить нужные проверки результата.\n\n",
                1,
            )
            task_path.write_text(generic_project_items, encoding="utf-8")
            _tasks, generic_project_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("is generic" in error for error in generic_project_errors) == 2, (
                real_adapter["platform_input"], generic_project_errors,
            )
            assert normalize_deliverable_unicode("файлы и настройки") == "файлы и настройки"
            generic_files_settings = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Подготовить необходимые файлы и настройки проекта для проверки результата.\n"
                "- Обновить требуемые настройки и файлы проекта для теста результата.\n\n",
                1,
            )
            task_path.write_text(generic_files_settings, encoding="utf-8")
            _tasks, generic_files_settings_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("is generic" in error for error in generic_files_settings_errors) == 2, (
                real_adapter["platform_input"], generic_files_settings_errors,
            )
            combining_generic_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Создать необхо́димые изменения в проекте и проверки результата.\n"
                "- Добавить тре́буемые файлы проекта и тесты проверки результата.\n\n",
                1,
            )
            task_path.write_text(combining_generic_items, encoding="utf-8")
            _tasks, combining_generic_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("is generic" in error for error in combining_generic_errors) == 2, (
                real_adapter["platform_input"], combining_generic_errors,
            )
            mixed_script_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Создать всe нeобходимыe изменения в проекте и проверки результата.\n"
                "- Добавить всe трeбуемыe файлы проекта и тесты проверки результата.\n\n",
                1,
            )
            task_path.write_text(mixed_script_items, encoding="utf-8")
            _tasks, mixed_script_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("mixed Cyrillic/Latin" in error for error in mixed_script_errors) == 2, (
                real_adapter["platform_input"], mixed_script_errors,
            )
            zero_width_generic_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Создать все необхо\u200bдимые изменения в проекте и проверки результата.\n"
                "- Добавить все тре\u200bбуемые файлы проекта и тесты проверки результата.\n\n",
                1,
            )
            task_path.write_text(zero_width_generic_items, encoding="utf-8")
            _tasks, zero_width_generic_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("is generic" in error for error in zero_width_generic_errors) == 2, (
                real_adapter["platform_input"], zero_width_generic_errors,
            )
            hyphen_fragment_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- а-б-в-г-д сохраняет выбранное состояние вкладки навигации.\n"
                "- a-b-c-d-e восстанавливает выбранное состояние экрана навигации.\n\n",
                1,
            )
            task_path.write_text(hyphen_fragment_items, encoding="utf-8")
            _tasks, hyphen_fragment_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("one-letter fragment chain" in error for error in hyphen_fragment_errors) == 2, (
                real_adapter["platform_input"], hyphen_fragment_errors,
            )
            punctuation_fragment_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- а.б.в.г.д сохраняет выбранное состояние вкладки навигации.\n"
                "- а/б/в/г/д восстанавливает выбранное состояние экрана навигации.\n\n",
                1,
            )
            task_path.write_text(punctuation_fragment_items, encoding="utf-8")
            _tasks, punctuation_fragment_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("one-letter fragment chain" in error for error in punctuation_fragment_errors) == 2, (
                real_adapter["platform_input"], punctuation_fragment_errors,
            )
            path_padding_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- `iOS/Sources/Feature.swift` — production файл.\n"
                "- `Android/src/FeatureTest.kt` — production файл.\n\n",
                1,
            )
            task_path.write_text(path_padding_items, encoding="utf-8")
            _tasks, path_padding_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("requires independent prose" in error for error in path_padding_errors) == 2, (
                real_adapter["platform_input"], path_padding_errors,
            )
            code_padding_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- `NavigationState` — Swift тип для REQ-1 и AC-1.\n"
                "- `SelectionStore` — Swift тип для REQ-1 и AC-1.\n\n",
                1,
            )
            task_path.write_text(code_padding_items, encoding="utf-8")
            _tasks, code_padding_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("requires independent prose" in error for error in code_padding_errors) == 2, (
                real_adapter["platform_input"], code_padding_errors,
            )
            id_padding_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- REQ-1 / AC-1 — product контракт и результат.\n"
                "- TST-REQ-1 / TST-AC-1 — product контракт и результат.\n\n",
                1,
            )
            task_path.write_text(id_padding_items, encoding="utf-8")
            _tasks, id_padding_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("is generic" in error for error in id_padding_errors) == 2, (
                real_adapter["platform_input"], id_padding_errors,
            )
            jargon_padding_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Флюксорная синхронизация завершена.\n"
                "- Квазимодульный оркестратор подготовлен.\n\n",
                1,
            )
            task_path.write_text(jargon_padding_items, encoding="utf-8")
            _tasks, jargon_padding_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("requires independent prose" in error for error in jargon_padding_errors) == 2, (
                real_adapter["platform_input"], jargon_padding_errors,
            )
            long_generic_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n"
                "- Подготовить все необходимые текущие изменения в проекте и требуемые проверки результата.\n"
                "- Обновить все нужные файлы проекта и необходимые тесты проверки результата.\n\n",
                1,
            )
            task_path.write_text(long_generic_items, encoding="utf-8")
            _tasks, long_generic_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert sum("is generic" in error for error in long_generic_errors) == 2, (
                real_adapter["platform_input"], long_generic_errors,
            )
            placeholder_items = synthetic_task.replace(
                deliverables_block,
                "## Implementation deliverables\n- Production файл `<artifact>`.\n- Focused test для границы поведения.\n\n",
                1,
            )
            task_path.write_text(placeholder_items, encoding="utf-8")
            _tasks, placeholder_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("unresolved placeholder" in error for error in placeholder_errors), (
                real_adapter["platform_input"], placeholder_errors,
            )
            missing_steps = synthetic_task.replace(
                "## Steps\nСоздать production файл.\n\n", "## Steps\n\n", 1,
            )
            task_path.write_text(missing_steps, encoding="utf-8")
            _tasks, missing_steps_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter,
                require_implementation_deliverables=True,
            )
            assert any("missing substantive section: Steps" in error for error in missing_steps_errors), (
                real_adapter["platform_input"], missing_steps_errors,
            )
            task_path.write_text(synthetic_task, encoding="utf-8")
            task_path.write_text(
                synthetic_task.replace(f"proposed: {writable_ref}", f"existing: {context_ref}"),
                encoding="utf-8",
            )
            _tasks, protected_errors = parse_tasks(
                synthetic_repo, package, adapter=real_adapter, validate_plan_paths=True,
                require_implementation_deliverables=True,
            )
            assert any("protected/excluded boundary" in error for error in protected_errors), (
                real_adapter["platform_input"], protected_errors,
            )
    with tempfile.TemporaryDirectory() as language_tmp:
        language_repo = Path(language_tmp)
        scenarios = {
            "english": "## Goal\n\nDeliver an accessible platform feature with deterministic behavior.\n",
            "padding": (
                "## Context\n\nЭтот абзац написан по-русски и описывает исходный контекст.\n\n"
                "## Goal\n\nDeliver an accessible platform feature with deterministic behavior.\n"
            ),
            "embedded": (
                "## Context\n\nКонтекст и ограничения реализации подробно описаны по-русски.\n\n"
                "## Risk\n\nThis paragraph remains entirely English inside the Russian document.\n"
            ),
            "russian-technical": (
                "## Goal\n\nSwiftUI и Liquid Glass формируют нативную поверхность, а Gradle и "
                "Material 3 остаются точными техническими названиями.\n"
            ),
            "machine-only": (
                "# Verification\n\n- Status: pending\n- Evidence: none\n"
                "- Read-only context: none\n"
                "- Paths: proposed: Android/features/app-shell/build.gradle.kts\n"
                "| Contract ID | Status |\n|---|---|\n| AND-REQ-1 | PASS |\n"
            ),
            "english-table": (
                "| Contract ID | Method | Status |\n|---|---|---|\n"
                "| AND-REQ-1 | Review deterministic platform behavior | pending |\n"
            ),
            "russian-table": (
                "| Contract ID | Method | Status |\n|---|---|---|\n"
                "| IOS-REQ-1 | Проверить поведение SwiftUI и Liquid Glass | PASS |\n"
            ),
            "machine-table": (
                "| Contract ID | Evidence path | Status |\n|---|---|---|\n"
                "| IOS-REQ-1 | evidence/req-1.md | PASS |\n"
            ),
            "english-link": (
                "[Detailed implementation guidance](https://example.com/guide)\n"
            ),
            "raw-url": "https://developer.example.com/reference/api\n",
            "russian-link": (
                "[Подробное руководство по реализации](https://example.com/guide)\n"
            ),
            "sibling-bullets": (
                "- Этот длинный русский пункт подробно описывает архитектурное решение и ограничения.\n"
                "- This separate bullet remains entirely English.\n"
            ),
            "numbered-continuation": (
                "1. Русский пункт начинается здесь и содержит подробное решение.\n"
                "   Его continuation line остаётся частью того же русского пункта.\n"
                "2. This separate numbered item remains English.\n"
            ),
            "machine-english-continuation": (
                "- Evidence: none\n"
                "  This continuation explains the evidence in English.\n"
            ),
            "machine-russian-continuation": (
                "- Evidence: none\n"
                "  Это отдельное русское пояснение к machine row.\n"
            ),
            "valid-utf8": "Корректный UTF-8 текст остаётся валидным.\n",
        }
        for adapter in real_adapters:
            platform_root = language_repo / str(adapter["platform_name"])
            platform_root.mkdir()
            language_package = platform_root / "change-package"
            language_package.mkdir()
            results: dict[str, list[str]] = {}
            for name, content in scenarios.items():
                path = language_package / f"{name}.md"
                path.write_text(content, encoding="utf-8")
                results[name] = validate_authored_markdown_language(
                    language_repo, language_package, path,
                )
            assert results["english"]
            assert results["padding"]
            assert results["embedded"]
            assert results["russian-technical"] == []
            assert results["machine-only"] == []
            assert results["english-table"]
            assert results["russian-table"] == []
            assert results["machine-table"] == []
            assert results["english-link"]
            assert results["raw-url"] == []
            assert results["russian-link"] == []
            assert results["sibling-bullets"] and "blocks 2" in results["sibling-bullets"][0]
            assert results["numbered-continuation"] and "blocks 2" in results["numbered-continuation"][0]
            assert results["machine-english-continuation"]
            assert results["machine-russian-continuation"] == []
            assert results["valid-utf8"] == []
            invalid_utf8 = language_package / "invalid-utf8.md"
            invalid_utf8.write_bytes(b"\xff\xfeinvalid authored bytes")
            invalid_utf8_errors = validate_authored_markdown_language(
                language_repo, language_package, invalid_utf8,
            )
            assert len(invalid_utf8_errors) == 1
            assert "invalid-utf8.md" in invalid_utf8_errors[0]
            assert "invalid authored bytes" not in invalid_utf8_errors[0]
            assert "UnicodeDecodeError" not in invalid_utf8_errors[0]
            target = language_package / "regular-target.md"
            target.write_text("Корректный русский текст для regular target.\n", encoding="utf-8")
            symlink = language_package / "symlink.md"
            symlink.symlink_to(target.name)
            symlink_errors = validate_authored_markdown_language(
                language_repo, language_package, symlink,
            )
            assert len(symlink_errors) == 1
            assert "regular authored Markdown file" in symlink_errors[0]
            assert "Корректный русский текст" not in symlink_errors[0]
            non_regular = language_package / "directory.md"
            non_regular.mkdir()
            non_regular_errors = validate_authored_markdown_language(
                language_repo, language_package, non_regular,
            )
            assert len(non_regular_errors) == 1
            assert "regular authored Markdown file" in non_regular_errors[0]
            external_plan = platform_root / "external-plan"
            external_plan.mkdir()
            (external_plan / "README.md").write_text(
                "Внешний русский текст не должен обходить package boundary.\n",
                encoding="utf-8",
            )
            plan = language_package / "plan"
            plan.symlink_to(external_plan, target_is_directory=True)
            external_ancestor_errors = validate_authored_markdown_language(
                language_repo, language_package, plan / "README.md",
            )
            assert len(external_ancestor_errors) == 1
            assert "safe regular authored Markdown file" in external_ancestor_errors[0]
            plan.unlink()

            real_plan = language_package / "real-plan"
            real_plan.mkdir()
            (real_plan / "README.md").write_text(
                "Обычный вложенный план содержит корректный русский текст.\n",
                encoding="utf-8",
            )
            plan.symlink_to(real_plan.name, target_is_directory=True)
            internal_ancestor_errors = validate_authored_markdown_language(
                language_repo, language_package, plan / "README.md",
            )
            assert len(internal_ancestor_errors) == 1
            assert "safe regular authored Markdown file" in internal_ancestor_errors[0]
            plan.unlink()
            plan.mkdir()
            normal_nested = plan / "README.md"
            normal_nested.write_text(
                "Обычный вложенный plan artifact написан по-русски.\n",
                encoding="utf-8",
            )
            assert validate_authored_markdown_language(
                language_repo, language_package, normal_nested,
            ) == []

            outside = platform_root / "outside.md"
            outside.write_text("Внешний файл написан по-русски.\n", encoding="utf-8")
            traversal = language_package / ".." / "outside.md"
            assert validate_authored_markdown_language(
                language_repo, language_package, traversal,
            )
            assert validate_authored_markdown_language(
                language_repo, language_package, outside,
            )

            real_package = platform_root / "real-change-package"
            real_package.mkdir()
            (real_package / "proposal.md").write_text(
                "Русский authored text находится в реальном package.\n",
                encoding="utf-8",
            )
            linked_package = platform_root / "linked-change-package"
            linked_package.symlink_to(real_package.name, target_is_directory=True)
            linked_package_errors = validate_authored_markdown_language(
                language_repo, linked_package, linked_package / "proposal.md",
            )
            assert len(linked_package_errors) == 1
            assert "safe regular authored Markdown file" in linked_package_errors[0]

            evidence = language_package / "evidence"
            evidence.mkdir()
            task_report = evidence / "task-001.md"
            task_report.write_text(
                "## Итог\n\nThis authored task report remains entirely English.\n",
                encoding="utf-8",
            )
            runtime_markdown = evidence / "runtime-output.md"
            runtime_markdown.write_text(
                "Русский raw runtime output не является authored padding.\n",
                encoding="utf-8",
            )
            (evidence / "runtime-output.log").write_text(
                "raw runtime log\n", encoding="utf-8",
            )
            (evidence / "runtime-output.json").write_text(
                '{"raw": "runtime output"}\n', encoding="utf-8",
            )
            selected_reports = typed_authored_report_paths(language_package)
            assert selected_reports == [task_report]
            english_task_errors = validate_task_evidence_language(
                language_repo, language_package, selected_reports[0],
            )
            assert english_task_errors
            assert "task-001.md" in english_task_errors[0]
            assert "entirely English" not in english_task_errors[0]
            task_report.write_text(
                "## Итог\n\nОтчёт задачи написан по-русски и фиксирует проверенный результат.\n",
                encoding="utf-8",
            )
            assert validate_task_evidence_language(
                language_repo, language_package, task_report,
            ) == []
            task_report.write_text(
                "## Итог\n\nThis standalone English sentence must remain invalid. "
                "Длинное русское пояснение подтверждает результат, описывает проверку, "
                "границы и наблюдаемое поведение, но не компенсирует английское предложение.\n",
                encoding="utf-8",
            )
            padding_errors = validate_task_evidence_language(
                language_repo, language_package, task_report,
            )
            assert padding_errors and "task-001.md" in padding_errors[0]
            task_report.write_text(
                "## Итог\n\nОтчёт задачи написан по-русски и фиксирует проверенный результат.\n",
                encoding="utf-8",
            )

            reconciliation_report = (
                evidence / "reconciliation-20260716T120000Z-task-001-platform-drift.md"
            )
            reconciliation_report.write_text(
                "This reconciliation report remains entirely English.\n",
                encoding="utf-8",
            )
            reconciliation_errors = validate_authored_markdown_language(
                language_repo, language_package, reconciliation_report,
            )
            assert len(reconciliation_errors) == 1
            reconciliation_report.write_text(
                "Отчёт reconciliation по-русски описывает согласованное исправление.\n",
                encoding="utf-8",
            )
            assert validate_authored_markdown_language(
                language_repo, language_package, reconciliation_report,
            ) == []

            typed_target = evidence / "typed-target.md"
            typed_target.write_text("Корректный русский target.\n", encoding="utf-8")
            typed_symlink = evidence / "task-002.md"
            typed_symlink.symlink_to(typed_target.name)
            assert validate_task_evidence_language(
                language_repo, language_package, typed_symlink,
            )
            invalid_typed = evidence / "task-003.md"
            invalid_typed.write_bytes(b"\xff\xfeinvalid typed report")
            invalid_typed_errors = validate_task_evidence_language(
                language_repo, language_package, invalid_typed,
            )
            assert len(invalid_typed_errors) == 1
            assert "invalid typed report" not in invalid_typed_errors[0]

            external_evidence = platform_root / "external-evidence"
            external_evidence.mkdir()
            (external_evidence / "task-004.md").write_text(
                "Внешний typed report не обходит ancestor boundary.\n",
                encoding="utf-8",
            )
            ancestor_package = platform_root / "ancestor-package"
            ancestor_package.mkdir()
            (ancestor_package / "evidence").symlink_to(
                external_evidence, target_is_directory=True,
            )
            ancestor_reports = typed_authored_report_paths(ancestor_package)
            assert len(ancestor_reports) == 1
            assert validate_task_evidence_language(
                language_repo, ancestor_package, ancestor_reports[0],
            )

            noisy = language_package / "noisy.md"
            noisy.write_text(
                "\n\n".join(
                    f"## Section {index}\n\nEnglish prose block number {index} remains invalid."
                    for index in range(1, 9)
                ),
                encoding="utf-8",
            )
            bounded = validate_authored_markdown_language(
                language_repo, language_package, noisy,
            )
            assert len(bounded) == 1 and "(+5 more)" in bounded[0]
    project_evidence = {
        "ios": "iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj",
        "android": "Android/settings.gradle.kts",
    }
    broad_triggers = "independent-feature=yes; domain-data=yes; network=yes; persistence=yes; reusable-ui=yes; consumers=3; independent-ownership=yes"
    tiny_triggers = "independent-feature=no; domain-data=no; network=no; persistence=no; reusable-ui=no; consumers=1; independent-ownership=no"
    for real_adapter in real_adapters:
        platform_input = str(real_adapter["platform_input"])
        config = real_adapter["modularity"]
        unit = str(config["physical_units"][0])
        evidence = f"{real_adapter['_path']}; {project_evidence[platform_input]}"
        scope = {str(config["isolation_scope"])}
        isolated = adapter_modularity_decision(
            real_adapter, "isolated", evidence,
            f"A proposed {unit} provides the cohesive capability boundary based on the discovered project graph.",
            broad_triggers,
        )
        assert validate_modularity_decision(repository_root(), real_adapter, isolated, scope) == []
        shell_ownership = isolated.replace(
            "The selected boundary balances cohesive ownership, visibility, consumer independence and build overhead.",
            "The application shell owns feature domain data network persistence reusable-UI implementation and mutable-state behavior.",
        )
        assert any("application shell" in error for error in validate_modularity_decision(repository_root(), real_adapter, shell_ownership, scope))
        inverse_shell_ownership = isolated.replace(
            "The selected boundary balances cohesive ownership, visibility, consumer independence and build overhead.",
            "Feature data and mutable-state implementation are owned by the application shell.",
        )
        assert any("application shell" in error for error in validate_modularity_decision(repository_root(), real_adapter, inverse_shell_ownership, scope))
        for forbidden_claim in (
            "Feature data network persistence implementation resides in the application shell.",
            "The application shell is responsible for feature data network persistence implementation and mutable state.",
            "Feature data network persistence implementation lives in the application shell.",
            "Feature data network persistence implementation is the responsibility of the application shell.",
            "Feature data network persistence implementation resides in the target of the app.",
            "Feature data network persistence and mutable state live in the app's target.",
            "The executable target of the application is responsible for feature data network persistence implementation and mutable state.",
            "The application host module owns feature data network persistence implementation and mutable state.",
            "Feature data network persistence implementation resides in the module belonging to the app.",
            "The application composition shell is responsible for feature data network persistence implementation and mutable state.",
            "Feature data network persistence implementation lives in the host shell of the app.",
        ):
            claimed = isolated.replace(
                "The selected boundary balances cohesive ownership, visibility, consumer independence and build overhead.",
                forbidden_claim,
            )
            claim_errors = validate_modularity_decision(
                repository_root(), real_adapter, claimed, scope
            )
            assert any("application shell" in error for error in claim_errors), (
                platform_input, forbidden_claim, claim_errors
            )
        extra_shell_prose = isolated.replace(
            "## Modularity decision\n\n",
            "## Modularity decision\n\nApplication shell contains feature implementation.\n",
        )
        assert any(
            "only the exact structured field rows" in error
            for error in validate_modularity_decision(
                repository_root(), real_adapter, extra_shell_prose, scope
            )
        )
        application_physical = isolated.replace(
            f"A proposed {unit} provides the cohesive capability boundary based on the discovered project graph.",
            "A proposed application target provides the capability boundary.",
        )
        assert any(
            "Physical boundaries cannot reference an application unit" in error
            for error in validate_modularity_decision(
                repository_root(), real_adapter, application_physical, scope
            )
        )
        broad_na = adapter_modularity_decision(
            real_adapter, "not-applicable", evidence,
            "The broad capability remains local without a new physical unit despite multiple consumers.",
            broad_triggers,
        )
        assert any("not-applicable requires all capability triggers" in error for error in validate_modularity_decision(repository_root(), real_adapter, broad_na, set()))
        folder_bypass = isolated.replace(
            f"A proposed {unit} provides the cohesive capability boundary based on the discovered project graph.",
            f"The feature folder provides the physical module boundary and is labelled as a proposed {unit}.",
        )
        assert any("folder/directory/layer/package-name" in error for error in validate_modularity_decision(repository_root(), real_adapter, folder_bypass, scope))
        fake_evidence = isolated.replace(evidence, "NoSuch/Constraint/file.txt")
        assert any("missing or unsafe" in error for error in validate_modularity_decision(repository_root(), real_adapter, fake_evidence, scope))
        bad_adapter = json.loads(json.dumps({key: value for key, value in real_adapter.items() if key != "_path"}))
        bad_adapter["modularity"]["physical_units"] = ["application target"]
        try:
            validate_profiles(repository_root(), bad_adapter)
            raise AssertionError(f"{platform_input} application physical unit passed adapter schema")
        except RuleProfileError as error:
            assert "non-application" in str(error)
        deviation = adapter_modularity_decision(
            real_adapter, "deviation", evidence,
            f"An existing discovered {unit} combines the related capabilities behind one public contract.",
            broad_triggers,
        )
        assert validate_modularity_decision(repository_root(), real_adapter, deviation, scope) == []
        tiny_na = adapter_modularity_decision(
            real_adapter, "not-applicable", evidence,
            "The tiny local behavior stays within its one existing cohesive owner and claims no physical unit.",
            tiny_triggers,
        )
        assert validate_modularity_decision(repository_root(), real_adapter, tiny_na, set()) == []
        unknown_verification = fixture_modularity_verification("UNKNOWN")
        assert validate_modularity_verification(unknown_verification, "implement") == []
        assert any("invalid status for verify: UNKNOWN" in error for error in validate_modularity_verification(unknown_verification, "verify"))
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); adapter, package, meta = write_fixture(repo)
        for capabilities in (
            ["plan", "propose"],
            ["propose", "implement"],
            ["propose", "plan", "implement", "archive-implementation"],
            ["propose", "plan", "implement", "verify", "archive-implementation", "unknown"],
        ):
            malformed = dict(adapter); malformed["lifecycle_capabilities"] = capabilities
            try:
                validate_profiles(repo, malformed)
                raise AssertionError("malformed capabilities passed")
            except RuleProfileError:
                pass
        mutated = dict(adapter); mutated["lifecycle_capabilities"] = ["propose", "plan", "implement"]
        try:
            validate_profiles(repo, mutated)
            raise AssertionError("disabled phase profile passed")
        except RuleProfileError:
            pass
        disabled = dict(adapter)
        disabled["lifecycle_capabilities"] = ["propose", "plan", "implement"]
        disabled["phase_rule_profiles"] = {
            phase: adapter["phase_rule_profiles"][phase] for phase in ("propose", "plan", "implement")
        }
        assert any("capability 'verify'" in error for error in validate_package(repo, disabled, "sample", "sample", "verify"))
        initial_errors = validate_package(repo, adapter, "sample", "sample", "propose")
        assert initial_errors == [], initial_errors
        missing_version = dict(meta)
        missing_version.pop("modularity_contract_version")
        (package / "meta.json").write_text(json.dumps(missing_version))
        missing_version_errors = validate_package(repo, adapter, "sample", "sample", "propose")
        assert any("sealed planned/implementing/verified package" in error for error in missing_version_errors), missing_version_errors
        future_version = dict(meta)
        future_version["modularity_contract_version"] = 2
        (package / "meta.json").write_text(json.dumps(future_version))
        future_version_errors = validate_package(repo, adapter, "sample", "sample", "propose")
        assert any("unsupported modularity_contract_version" in error for error in future_version_errors), future_version_errors
        (package / "meta.json").write_text(json.dumps(meta))
        original_design = (package / "design.md").read_text()
        base_decision = fixture_modularity_decision()
        (package / "design.md").write_text(original_design.replace(base_decision, ""))
        assert any("missing Modularity decision" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        isolated_design = original_design.replace(base_decision, fixture_modularity_decision("isolated"))
        (package / "design.md").write_text(isolated_design)
        assert any("requires engineering scope: package" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        blocked_design = original_design.replace("- Boundary guard verdict: PASS", "- Boundary guard verdict: BLOCK")
        (package / "design.md").write_text(blocked_design)
        assert any("exact Boundary guard verdict: PASS" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        deviation = fixture_modularity_decision("deviation")
        weak_deviation = deviation.replace(
            "TestClient/workflow/package.md; TestClient/workflow/platform-contract.json",
            "NoSuch/Constraint/file.txt",
        )
        (package / "design.md").write_text(original_design.replace(base_decision, weak_deviation))
        assert any("missing or unsafe" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        folder_module = base_decision.replace(
            "The tiny local behavior remains within its existing cohesive owner; no new physical unit is proposed.",
            "The feature folder is a physical module and therefore provides the required isolation boundary.",
        )
        (package / "design.md").write_text(original_design.replace(base_decision, folder_module))
        folder_errors = validate_package(repo, adapter, "sample", "sample", "propose")
        assert any("folder/directory/layer/package-name" in error for error in folder_errors), folder_errors
        isolated_meta = dict(meta)
        isolated_meta["engineering_scopes"] = ["application", "package"]
        isolated_meta["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/package.md",
        ]
        isolated_with_scope = isolated_design.replace(
            "- application: Typed application boundaries and deterministic tests apply to this change.",
            "- application: Typed application boundaries and deterministic tests apply to this change.\n"
            "- package: The Test package provides the selected physical isolation boundary.",
        )
        (package / "meta.json").write_text(json.dumps(isolated_meta))
        (package / "design.md").write_text(isolated_with_scope)
        propose_errors = validate_package(repo, adapter, "sample", "sample", "propose")
        assert propose_errors == [], propose_errors
        deviation_with_scope = original_design.replace(base_decision, deviation).replace(
            "- application: Typed application boundaries and deterministic tests apply to this change.",
            "- application: Typed application boundaries and deterministic tests apply to this change.\n"
            "- package: The existing Test library package preserves the selected physical isolation boundary.",
        )
        (package / "design.md").write_text(deviation_with_scope)
        deviation_errors = validate_package(repo, adapter, "sample", "sample", "propose")
        assert deviation_errors == [], deviation_errors
        (package / "meta.json").write_text(json.dumps(meta))
        (package / "design.md").write_text(original_design)
        adapter_path = repo / str(adapter["_path"])
        adapter_source = adapter_path.read_text()
        malformed_adapter = {key: value for key, value in adapter.items() if key != "_path"}
        malformed_adapter["platform_ux"] = {"role": "broken"}
        adapter_path.write_text(json.dumps(malformed_adapter))
        try:
            load_adapter(repo, "test-client")
            raise AssertionError("malformed platform_ux adapter schema passed")
        except AdapterError as error:
            assert "platform_ux" in str(error)
        adapter_path.write_text(adapter_source)
        malformed_adapter = {key: value for key, value in adapter.items() if key != "_path"}
        malformed_adapter["modularity"] = {"isolation_scope": "missing"}
        adapter_path.write_text(json.dumps(malformed_adapter))
        try:
            load_adapter(repo, "test-client")
            raise AssertionError("malformed modularity adapter schema passed")
        except AdapterError as error:
            assert "modularity" in str(error)
        adapter_path.write_text(adapter_source)
        ux_artifact = package / "platform-ux.md"
        ux_source = fixture_platform_ux(adapter)
        assert validate_package(repo, adapter, "sample", "sample", "propose") == []
        ux_artifact.write_text(ux_source)
        assert any("unexpected outside" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        ux_artifact.unlink()
        technical = dict(meta)
        technical.update(
            change_type="technical-only", shared_product_spec=None,
            product_status="N/A", product_approval="N/A", product_impact="NONE",
            impact_evidence="Репозиторная инфраструктура не влияет на наблюдаемое продуктовое поведение.",
        )
        (package / "meta.json").write_text(json.dumps(technical))
        assert validate_package(repo, adapter, "sample", "sample", "propose") == []
        ux_artifact.write_text(ux_source)
        assert any("unexpected outside" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        ux_artifact.unlink()
        (package / "meta.json").write_text(json.dumps(meta))
        bad_meta = dict(meta); bad_meta["engineering_scopes"] = ["unknown"]
        (package / "meta.json").write_text(json.dumps(bad_meta))
        assert any("unknown engineering scope" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        bad_meta = dict(meta); bad_meta["applicable_rule_files"] = ["TestClient/workflow/base.md"]
        (package / "meta.json").write_text(json.dumps(bad_meta))
        assert any("exactly match" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        bad_meta = dict(meta); bad_meta["applicable_rule_files"] = list(meta["applicable_rule_files"]) + ["TestClient/workflow/performance-a.md"]
        (package / "meta.json").write_text(json.dumps(bad_meta))
        assert any("exactly match" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        bad_meta = dict(meta); bad_meta["applicable_rule_files"] = ["../escape.md"]
        (package / "meta.json").write_text(json.dumps(bad_meta))
        assert any("exactly match" in error for error in validate_package(repo, adapter, "sample", "sample", "propose"))
        (package / "meta.json").write_text(json.dumps(meta))
        assert resolve_change(repo, adapter, "sample", None, "plan")[0] == "sample"
        try: resolve_change(repo, adapter, "../bad", None, "plan"); raise AssertionError("traversal passed")
        except AdapterError: pass
        other = package.parent / "other"; other.mkdir(); (other/"meta.json").write_text("{}")
        try: resolve_change(repo, adapter, "sample", None, "plan"); raise AssertionError("ambiguity passed")
        except AdapterError: pass
        (other/"meta.json").unlink()
        try: resolve_change(repo, adapter, "sample", None, "plan"); raise AssertionError("partial sibling passed")
        except AdapterError: pass
        assert resolve_change(repo, adapter, "sample", "sample", "plan")[0] == "sample"
        other.rmdir()
        tombstone = package.parent / "old-change"; tombstone.mkdir()
        (tombstone / "ARCHIVED.md").write_text("# Archived\n")
        assert resolve_change(repo, adapter, "sample", None, "plan")[0] == "sample"
        junk = package.parent / "owner-note.txt"; junk.write_text("unclassified sibling\n")
        try: resolve_change(repo, adapter, "sample", None, "plan"); raise AssertionError("junk direct child passed omission")
        except AdapterError: pass
        assert resolve_change(repo, adapter, "sample", "sample", "plan")[0] == "sample"
        junk.unlink()
        (tombstone / "extra.txt").write_text("extra tombstone state\n")
        try: resolve_change(repo, adapter, "sample", None, "plan"); raise AssertionError("non-tombstone-only child passed omission")
        except AdapterError: pass
        assert resolve_change(repo, adapter, "sample", "sample", "plan")[0] == "sample"
        (tombstone / "extra.txt").unlink(); shutil.rmtree(tombstone)
        linked = package.parent / "linked-change"; linked.symlink_to(package.name, target_is_directory=True)
        try: resolve_change(repo, adapter, "sample", None, "plan"); raise AssertionError("symlink direct child passed omission")
        except AdapterError: pass
        assert resolve_change(repo, adapter, "sample", "sample", "plan")[0] == "sample"
        linked.unlink()

        plan = package/"plan"; plan.mkdir()
        (plan/"README.md").write_text("# Plan\n\n## Planning frame\nImplement three bounded tasks after approved specification.\n\n## Revalidated engineering scopes and exact rules\n- Engineering scopes: [\"application\"]\n- Applicable rule files: [\"TestClient/workflow/base.md\", \"TestClient/workflow/application.md\"]\n\n## DAG\ntask-001 precedes dependent task-002; task-003 is independent.\n\n## Estimates and multipliers\nThe estimate includes greenfield integration uncertainty.\n\n## Verification strategy\nRun focused boundary and integration tests.\n")
        task = "# task-001\n- Layer: domain\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Sources/Sample.swift\n\n## Goal\nCreate the typed platform behavior boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes its deterministic result.\n\n## Implementation deliverables\n- Typed platform behavior boundary in `Sample.swift`.\n- Focused boundary behavior test with deterministic result.\n\n## Steps\nImplement the typed boundary and its focused behavior test.\n\n## Verification\nRun the focused deterministic boundary test.\n\n## Expected result\nThe boundary returns the expected typed result.\n\n## Out of scope\nOther features and unrelated platform cleanup remain excluded.\n"
        task_2 = "# task-002\n- Layer: tests\n- Engineering scopes: [\"application\"]\n- Depends on: task-001\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Tests/SampleTests.swift\n\n## Goal\nVerify the dependent shared behavior integration.\n\n## Inline contract context\nREQ-1 defines shared behavior and AC-1 observes the integrated result.\n\n## Implementation deliverables\n- Shared behavior integration scenario in `SampleTests.swift`.\n- Deterministic integration assertion for the approved result.\n\n## Steps\nAdd the dependent integration scenario after the boundary task.\n\n## Verification\nRun the focused shared integration test.\n\n## Expected result\nThe dependent integration test records the expected result.\n\n## Out of scope\nPlatform boundary changes remain owned by task-001.\n"
        task_3 = "# task-003\n- Layer: tests\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Tests/IndependentTests.swift\n\n## Goal\nVerify an independent owner of the platform acceptance criterion.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the independent result.\n\n## Implementation deliverables\n- Independent acceptance scenario in `IndependentTests.swift`.\n- Focused assertion for the typed boundary result.\n\n## Steps\nAdd the independent focused acceptance scenario.\n\n## Verification\nRun the independent deterministic acceptance test.\n\n## Expected result\nThe independent test records the expected boundary result.\n\n## Out of scope\nDependent integration remains owned by task-002.\n"
        task = task.replace("- Layer: domain\n", "- Layer: domain\n- Boundary owner: Sample capability boundary\n", 1)
        task_2 = task_2.replace("- Layer: tests\n", "- Layer: tests\n- Boundary owner: Sample integration test boundary\n", 1)
        task_3 = task_3.replace("- Layer: tests\n", "- Layer: tests\n- Boundary owner: Sample independent test boundary\n", 1)
        task = task.replace("- Paths:", "- Read-only context: none\n- Paths:", 1)
        task_2 = task_2.replace("- Paths:", "- Read-only context: none\n- Paths:", 1)
        task_3 = task_3.replace("- Paths:", "- Read-only context: none\n- Paths:", 1)
        (plan/"task-001.md").write_text(task)
        (plan/"task-002.md").write_text(task_2)
        (plan/"task-003.md").write_text(task_3)
        planned=dict(meta); planned.update(status="planned",tasks_total=3,rule_selection_snapshot="plan/rule-selection.json")
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(planned)))
        (package/"meta.json").write_text(json.dumps(planned))
        assert validate_package(repo, adapter, "sample", "sample", "plan") == []
        protected_plan_task = task.replace(
            "proposed: TestClient/Sources/Sample.swift",
            "existing: TestClient/specs/sample/changes/sample/meta.json",
        )
        (plan / "task-001.md").write_text(protected_plan_task)
        protected_plan_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("protected/excluded boundary" in error for error in protected_plan_errors), protected_plan_errors
        context_task = task.replace(
            "Read-only context: none",
            'Read-only context: ["TestClient/specs/sample/changes/sample/meta.json"]',
        )
        (plan / "task-001.md").write_text(context_task)
        assert validate_package(repo, adapter, "sample", "sample", "plan") == []
        existing_source = repo / "TestClient/Sources/Sample.swift"
        existing_source.parent.mkdir(parents=True); existing_source.write_text("struct Sample {}\n")
        proposed_existing_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("proposed path already exists" in error for error in proposed_existing_errors)
        existing_source.unlink(); existing_source.parent.rmdir()
        missing_existing_task = task.replace(
            "proposed: TestClient/Sources/Sample.swift",
            "existing: TestClient/Sources/Missing.swift",
        )
        (plan / "task-001.md").write_text(missing_existing_task)
        missing_existing_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("existing path does not exist" in error for error in missing_existing_errors)
        overlap_task = task.replace(
            "TestClient/Sources/Sample.swift", "TestClient/Sources"
        )
        overlap_task_2 = task_2.replace(
            "TestClient/Tests/SampleTests.swift", "TestClient/Sources/SampleTests.swift"
        )
        (plan / "task-001.md").write_text(overlap_task)
        (plan / "task-002.md").write_text(overlap_task_2)
        overlap_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("writable Paths overlap" in error for error in overlap_errors), overlap_errors
        (plan / "task-001.md").write_text(task)
        (plan / "task-002.md").write_text(task_2)
        legacy = dict(planned)
        legacy.pop("modularity_contract_version")
        legacy_design = (package / "design.md").read_text().replace(fixture_modularity_decision(), "")
        legacy_verification = (package / "verification.md").read_text().replace(fixture_modularity_verification(), "")
        legacy_task = task.replace("- Boundary owner: Sample capability boundary\n", "", 1)
        legacy_task_2 = task_2.replace("- Boundary owner: Sample integration test boundary\n", "", 1)
        legacy_task_3 = task_3.replace("- Boundary owner: Sample independent test boundary\n", "", 1)
        (package / "meta.json").write_text(json.dumps(legacy))
        (package / "design.md").write_text(legacy_design)
        (package / "verification.md").write_text(legacy_verification)
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(legacy)))
        (plan / "task-001.md").write_text(legacy_task)
        (plan / "task-002.md").write_text(legacy_task_2)
        (plan / "task-003.md").write_text(legacy_task_3)
        unregistered_errors = validate_package(repo, adapter, "sample", "sample", "implement")
        assert any("registry is missing" in error for error in unregistered_errors), unregistered_errors
        write_fixture_legacy_registry(repo, package, legacy)
        legacy_implement_errors = validate_package(repo, adapter, "sample", "sample", "implement")
        assert legacy_implement_errors == [], legacy_implement_errors
        forged_identity = dict(legacy)
        forged_identity["feature"] = "forged-sample"
        try:
            package_contract_version(repo, adapter, forged_identity, package, "implement")
            raise AssertionError("fresh sealed-looking legacy identity passed registry anchor")
        except AdapterError as error:
            assert "identity is not registered" in str(error)

        immutable_design = (package / "design.md").read_text()
        (package / "design.md").write_text(immutable_design + "\nForged design expansion.\n")
        design_drift_errors = validate_package(repo, adapter, "sample", "sample", "implement")
        assert any("design_sha256" in error for error in design_drift_errors), design_drift_errors
        (package / "design.md").write_text(immutable_design)

        (plan / "task-004.md").write_text(legacy_task_3.replace("task-003", "task-004", 1))
        added_task_errors = validate_package(repo, adapter, "sample", "sample", "implement")
        assert any("task_graph_sha256" in error for error in added_task_errors), added_task_errors
        (plan / "task-004.md").unlink()
        (plan / "task-003.md").unlink()
        removed_task_errors = validate_package(repo, adapter, "sample", "sample", "implement")
        assert any("task_graph_sha256" in error for error in removed_task_errors), removed_task_errors
        (plan / "task-003.md").write_text(legacy_task_3)
        for before, after in (
            ("proposed: TestClient/Sources/Sample.swift", "proposed: TestClient/Sources/Changed.swift"),
            ('Engineering scopes: ["application"]', 'Engineering scopes: ["application", "package"]'),
            ("Depends on: none", "Depends on: task-003"),
        ):
            (plan / "task-001.md").write_text(legacy_task.replace(before, after, 1))
            task_drift_errors = validate_package(repo, adapter, "sample", "sample", "implement")
            assert any("task_graph_sha256" in error for error in task_drift_errors), (
                before, after, task_drift_errors
            )
        (plan / "task-001.md").write_text(legacy_task)
        for field, value in (
            ("engineering_scopes", ["application", "package"]),
            ("applicable_rule_files", ["TestClient/workflow/base.md"]),
            ("tasks_total", 4),
            ("blocking_questions", ["Forged historical question"]),
        ):
            drifted_meta = dict(legacy)
            drifted_meta[field] = value
            (package / "meta.json").write_text(json.dumps(drifted_meta))
            meta_drift_errors = validate_package(repo, adapter, "sample", "sample", "implement")
            assert any("meta_identity_sha256" in error for error in meta_drift_errors), (
                field, meta_drift_errors
            )
            try:
                package_contract_version(repo, adapter, drifted_meta, package, "implement")
                raise AssertionError(f"legacy common resolver accepted immutable meta drift: {field}")
            except AdapterError:
                pass
        extra_meta = dict(legacy)
        extra_meta["forged_extension"] = "untrusted"
        (package / "meta.json").write_text(json.dumps(extra_meta))
        extra_meta_errors = validate_package(repo, adapter, "sample", "sample", "implement")
        assert any("exact historical key set" in error for error in extra_meta_errors), extra_meta_errors
        try:
            package_contract_version(repo, adapter, extra_meta, package, "implement")
            raise AssertionError("legacy common resolver accepted an extra meta key")
        except AdapterError as error:
            assert "unexpected: forged_extension" in str(error)
        (package / "meta.json").write_text(json.dumps(legacy))

        forged_package = repo / "TestClient/specs/forged-v0/changes/forged-v0"
        shutil.copytree(package, forged_package)
        forged_meta_path = forged_package / "meta.json"
        forged_meta = json.loads(forged_meta_path.read_text())
        forged_meta.update(feature="forged-v0", change_id="forged-v0")
        forged_meta_path.write_text(json.dumps(forged_meta))
        registry_path = repo / LEGACY_REGISTRY_PATH
        extended_registry = json.loads(registry_path.read_text())
        extended_registry["packages"].append(
            {
                "platform": "TestClient",
                "feature": "forged-v0",
                "change_id": "forged-v0",
                "package_path": forged_package.relative_to(repo).as_posix(),
                "hashes": legacy_package_hashes(forged_package, forged_meta),
            }
        )
        registry_path.write_text(json.dumps(extended_registry))
        copied_package_errors = validate_package(
            repo, adapter, "forged-v0", "forged-v0", "implement"
        )
        assert any("code-pinned canonical trust anchor" in error for error in copied_package_errors), copied_package_errors
        shutil.rmtree(forged_package.parents[1])
        write_fixture_legacy_registry(repo, package, legacy)
        lifecycle_meta = dict(legacy)
        lifecycle_meta.update(
            status="implementing", tasks_done=3, verification_status="pending",
            problems=[], verified_at=None, verification_state=None,
        )
        evidence_dir = package / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        for index, source_task in enumerate((legacy_task, legacy_task_2, legacy_task_3), start=1):
            evidence_ref = f"evidence/legacy-task-{index:03}.md"
            (plan / f"task-{index:03}.md").write_text(
                source_task.replace("Status: pending", "Status: done").replace(
                    "Evidence: none", f"Evidence: {evidence_ref}"
                )
            )
            (package / evidence_ref).write_text("Legacy lifecycle evidence.\n")
        (package / "meta.json").write_text(json.dumps(lifecycle_meta))
        assert package_contract_version(repo, adapter, lifecycle_meta, package, "implement") == 0
        for index, source_task in enumerate((legacy_task, legacy_task_2, legacy_task_3), start=1):
            (plan / f"task-{index:03}.md").write_text(source_task)
            (evidence_dir / f"legacy-task-{index:03}.md").unlink()
        evidence_dir.rmdir()
        (package / "meta.json").write_text(json.dumps(legacy))

        legacy_plan_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("cannot run Propose or Plan" in error for error in legacy_plan_errors), legacy_plan_errors
        (package / "meta.json").write_text(json.dumps(planned))
        (package / "design.md").write_text(original_design)
        (package / "verification.md").write_text(
            "# Verification\n\n" + fixture_modularity_verification()
            + "\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | approval record | pending |\n| AC-1 | integration | Run shared scenario | scenario report | pending |\n| TST-REQ-1 | design | Review current boundary | review record | pending |\n| TST-AC-1 | unit | Run focused boundary test | test report | pending |\n"
        )
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(planned)))
        (plan / "task-001.md").write_text(task)
        (plan / "task-002.md").write_text(task_2)
        (plan / "task-003.md").write_text(task_3)
        (plan / "task-001.md").write_text(task.replace("- Boundary owner: Sample capability boundary\n", "", 1))
        assert any("Boundary owner" in error for error in validate_package(repo, adapter, "sample", "sample", "plan"))
        (plan / "task-001.md").write_text(task)
        original_design = (package / "design.md").read_text()
        expanded = dict(planned)
        expanded["engineering_scopes"] = ["application", "performance"]
        expanded["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/performance-a.md", "TestClient/workflow/performance-b.md",
        ]
        (package / "meta.json").write_text(json.dumps(expanded))
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(expanded)))
        expanded_task = task.replace(
            '["application"]', '["application", "performance"]'
        ).replace(
            "Run the focused deterministic boundary test.",
            "Run the focused deterministic boundary test against the performance budget.",
        )
        (plan / "task-001.md").write_text(expanded_task)
        assert any("design Applied engineering scopes" in error for error in validate_package(repo, adapter, "sample", "sample", "plan"))
        (package / "design.md").write_text(original_design.replace(
            "- application: Typed application boundaries and deterministic tests apply to this change.",
            "- application: Typed application boundaries and deterministic tests apply to this change.\n- performance: Measurement rules apply to the selected performance work.",
        ))
        assert validate_package(repo, adapter, "sample", "sample", "plan") == []
        conditional = dict(planned)
        conditional["engineering_scopes"] = ["application", "localization", "ui"]
        conditional["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/localization.md", "TestClient/workflow/ui.md",
        ]
        conditional_design = original_design.replace(
            "- application: Typed application boundaries and deterministic tests apply to this change.",
            "- application: Typed application boundaries and deterministic tests apply to this change.\n- localization: Localized resources require a conditional task check.\n- ui: UI automation requires runtime and accessibility checks.\n\n## Platform UX trace and decisions\nThe architecture consumes platform-ux.md and preserves its native component, appearance and fallback decisions.",
        )
        (package / "design.md").write_text(conditional_design)
        (package / "meta.json").write_text(json.dumps(conditional))
        original_verification = (package / "verification.md").read_text()
        (package / "verification.md").write_text(
            original_verification
            + "\n## Native UX verification\n\nCapture native appearance, accessibility, light/dark and fallback evidence.\n"
            + native_obligation_table()
        )
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(conditional)))
        ui_test_task = task_2.replace('["application"]', '["application", "ui"]')
        localized_resource_task = task_3.replace('["application"]', '["application", "localization"]')
        (plan / "task-001.md").write_text(task)
        (plan / "task-002.md").write_text(ui_test_task)
        (plan / "task-003.md").write_text(localized_resource_task)
        assert any("requires platform-ux.md" in error for error in validate_package(repo, adapter, "sample", "sample", "plan"))
        ux_artifact.write_text(ux_source)
        for before, after, expected in (
            ("`TestClient`", "`WrongClient`", "Platform must be exactly"),
            ("`Native Test UI`", "`Wrong UI`", "Native design language adapter"),
            ("`soft blue`", "`red`", "Color direction"),
            ("`specs/product/sample/ux.md`", "`specs/product/other/ux.md`", "Source product UX"),
            ("`READY`", "`GAPS`", "UX status"),
            ("None.", "Unresolved native gap.", "Open gaps"),
            ("native-term-marker", "missing-native-marker", "required native term"),
        ):
            ux_artifact.write_text(ux_source.replace(before, after, 1))
            pressure_errors = validate_package(repo, adapter, "sample", "sample", "plan")
            assert any(expected in error for error in pressure_errors), (before, after, pressure_errors)
        for duplicate_line, label in (
            ("- **Color direction:** `red`", "Color direction"),
            ("- **UX status:** `GAPS`", "UX status"),
            ("- **Source product UX:** `specs/product/other/ux.md`", "Source product UX"),
        ):
            duplicated = ux_source.replace(
                "## Evidence inspected", f"{duplicate_line}\n\n## Evidence inspected", 1
            )
            ux_artifact.write_text(duplicated)
            assert any(
                f"{label} metadata must appear exactly once" in error
                for error in validate_package(repo, adapter, "sample", "sample", "plan")
            )
        ux_artifact.write_text(ux_source + "\n## Open gaps\n\nUnresolved native conflict.\n")
        assert any(
            "heading must appear exactly once: Open gaps" in error
            for error in validate_package(repo, adapter, "sample", "sample", "plan")
        )
        ux_artifact.write_text(
            ux_source + "\n## Evidence inspected\n\nConflicting second evidence account.\n"
        )
        assert any(
            "heading must appear exactly once: Evidence inspected" in error
            for error in validate_package(repo, adapter, "sample", "sample", "plan")
        )
        ux_artifact.write_text(ux_source.replace("## Motion and interaction", "## Missing motion section", 1))
        assert any(
            "heading must appear exactly once: Motion and interaction" in error
            for error in validate_package(repo, adapter, "sample", "sample", "plan")
        )
        resolved_section = (
            "Repository SDK, dependency, deployment and existing component evidence was inspected. "
            "Native behavior maps the shared intent with accessible fallbacks."
        )
        unknown_sections = ux_source.replace(
            resolved_section,
            "UNKNOWN repository SDK/dependency/deployment/component evidence remains unavailable",
        )
        ux_artifact.write_text(unknown_sections)
        assert any(
            "unresolved readiness markers" in error
            for error in validate_platform_ux(repo, adapter, package, "sample", conditional, {"application", "localization", "ui"})
        )
        gaps_sections = ux_source.replace(resolved_section, "GAPS remain in native availability evidence")
        ux_artifact.write_text(gaps_sections)
        assert any(
            "unresolved readiness markers" in error
            for error in validate_platform_ux(repo, adapter, package, "sample", conditional, {"application", "localization", "ui"})
        )
        gap_section = ux_source.replace(
            resolved_section,
            "GAP remains in repository SDK dependency deployment evidence",
            1,
        )
        ux_artifact.write_text(gap_section)
        assert any(
            "unresolved readiness markers" in error
            for error in validate_platform_ux(repo, adapter, package, "sample", conditional, {"application", "localization", "ui"})
        )
        allowed_unavailable = ux_source.replace(
            resolved_section,
            "The API is unavailable on an older OS; the documented standard-component fallback preserves behavior.",
        )
        ux_artifact.write_text(allowed_unavailable)
        allowed_unavailable_errors = validate_platform_ux(
            repo, adapter, package, "sample", conditional, {"application", "localization", "ui"}
        )
        assert allowed_unavailable_errors == [], allowed_unavailable_errors
        for false_none in ("No open questions.", "Нет открытых вопросов."):
            ux_artifact.write_text(ux_source.replace("None.", false_none, 1))
            assert any(
                "Open gaps must be exact None" in error
                for error in validate_platform_ux(repo, adapter, package, "sample", conditional, {"application", "localization", "ui"})
            )
        ux_artifact.write_text(ux_source + "\nTODO unresolved placeholder\n")
        assert any("contains placeholders" in error for error in validate_package(repo, adapter, "sample", "sample", "plan"))
        ux_artifact.write_text(ux_source)
        conditional_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("task-002 missing ui scope check" in error for error in conditional_errors)
        assert any("task-003 missing localization scope check" in error for error in conditional_errors)
        assert any("task-002 missing native UX check" in error for error in conditional_errors)
        ui_test_task_green = ui_test_task.replace(
            "Run the focused shared integration test.",
            "Run simulator UI automation with accessibility and design-system checks from platform-ux.md using Native Test UI, light/dark and fallback scenarios.",
        )
        localized_resource_green = localized_resource_task.replace(
            "Run the independent deterministic acceptance test.",
            "Run the independent localization resource acceptance test.",
        )
        (plan / "task-002.md").write_text(ui_test_task_green)
        (plan / "task-003.md").write_text(localized_resource_green)
        assert validate_package(repo, adapter, "sample", "sample", "plan") == []
        conditional_tasks, conditional_task_errors = parse_tasks(repo, package, adapter=adapter)
        assert conditional_task_errors == [], conditional_task_errors
        affected_native = affected_tasks_for_problem(
            conditional_tasks, {}, "NATIVE-ASSISTIVE-SEMANTICS"
        )
        assert [task["id"] for task in affected_native] == ["task-002"]
        native_verification = (package / "verification.md").read_text(encoding="utf-8")
        missing_native = native_verification.replace(
            "| NATIVE-TEXT-SCALING | pending | pending |\n", "", 1
        )
        _native_status, missing_native_errors = validate_native_obligations(
            package, missing_native, "plan"
        )
        assert any("NATIVE-TEXT-SCALING" in error and "missing" in error for error in missing_native_errors)
        native_evidence = package / "evidence"; native_evidence.mkdir(exist_ok=True)
        underlying = native_evidence / "native-underlying.txt"
        underlying.write_text("Наблюдаемое native evidence.\n", encoding="utf-8")
        terminal_rows: list[str] = []
        for obligation in NATIVE_OBLIGATION_IDS:
            record_ref = f"evidence/{obligation.casefold()}.json"
            (package / record_ref).write_text(json.dumps({
                "schema_version": 1,
                "obligation_id": obligation,
                "status": "PASS",
                "observation": "Отдельное наблюдение подтверждает эту native dimension.",
                "evidence_refs": ["evidence/native-underlying.txt"],
            }, ensure_ascii=False), encoding="utf-8")
            terminal_rows.append(f"| {obligation} | {record_ref} | PASS |")
        terminal_native = (
            "## Native obligation coverage\n\n"
            "| Obligation ID | Observation record | Status |\n|---|---|---|\n"
            + "\n".join(terminal_rows) + "\n"
        )
        _native_status, terminal_native_errors = validate_native_obligations(
            package, terminal_native, "verify"
        )
        assert terminal_native_errors == [], terminal_native_errors
        appearance_record = package / "evidence/native-appearance.json"
        light_record = package / "evidence/native-light.json"
        appearance_data = json.loads(appearance_record.read_text(encoding="utf-8"))
        light_data = json.loads(light_record.read_text(encoding="utf-8"))
        appearance_data["evidence_refs"] = ["evidence/native-light.json"]
        appearance_record.write_text(json.dumps(appearance_data, ensure_ascii=False), encoding="utf-8")
        _native_status, cross_record_errors = validate_native_obligations(
            package, terminal_native, "verify"
        )
        assert any(
            "cannot reference observation record: NATIVE-APPEARANCE" in error
            for error in cross_record_errors
        )
        light_data["evidence_refs"] = ["evidence/native-appearance.json"]
        light_record.write_text(json.dumps(light_data, ensure_ascii=False), encoding="utf-8")
        _native_status, cycle_errors = validate_native_obligations(
            package, terminal_native, "verify"
        )
        assert sum("cannot reference observation record" in error for error in cycle_errors) >= 2
        appearance_data["evidence_refs"] = ["evidence/native-underlying.txt"]
        light_data["evidence_refs"] = ["evidence/native-underlying.txt"]
        appearance_record.write_text(json.dumps(appearance_data, ensure_ascii=False), encoding="utf-8")
        light_record.write_text(json.dumps(light_data, ensure_ascii=False), encoding="utf-8")
        mismatch_record = package / "evidence/native-text-scaling.json"
        mismatch_data = json.loads(mismatch_record.read_text(encoding="utf-8"))
        mismatch_data["status"] = "UNKNOWN"
        mismatch_record.write_text(json.dumps(mismatch_data, ensure_ascii=False), encoding="utf-8")
        _native_status, mismatch_errors = validate_native_obligations(
            package, terminal_native, "verify"
        )
        assert any("row/record status mismatch: NATIVE-TEXT-SCALING" in error for error in mismatch_errors)
        mismatch_data["status"] = "PASS"
        mismatch_record.write_text(json.dumps(mismatch_data, ensure_ascii=False), encoding="utf-8")
        presentation_without_ui = task.replace("Layer: domain", "Layer: presentation")
        (plan / "task-001.md").write_text(presentation_without_ui)
        assert any("presentation task must include ui" in error for error in validate_package(repo, adapter, "sample", "sample", "plan"))
        ux_artifact.unlink()
        pressure = dict(planned)
        pressure["engineering_scopes"] = ["application", "networking", "package", "performance", "startup"]
        pressure["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/networking.md", "TestClient/workflow/package.md",
            "TestClient/workflow/performance-a.md", "TestClient/workflow/performance-b.md",
            "TestClient/workflow/startup.md",
        ]
        pressure_design = original_design.replace(
            "- application: Typed application boundaries and deterministic tests apply to this change.",
            "- application: Typed application boundaries and deterministic tests apply to this change.\n"
            "- networking: Cache and retry behavior require explicit planning.\n"
            "- package: Consumer and build boundaries require explicit planning.\n"
            "- performance: Measurement budget applies to this task.\n"
            "- startup: Launch budget applies to this task.",
        )
        generic_pressure_task = task.replace(
            '["application"]', '["application", "networking", "package", "performance", "startup"]'
        ).replace(
            "Run the focused deterministic boundary test.",
            "Run the focused test with a performance budget and launch budget.",
        )
        (package / "meta.json").write_text(json.dumps(pressure))
        (package / "design.md").write_text(pressure_design)
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(pressure)))
        (plan / "task-001.md").write_text(generic_pressure_task)
        (plan / "task-002.md").write_text(task_2)
        (plan / "task-003.md").write_text(task_3)
        pressure_errors = validate_package(repo, adapter, "sample", "sample", "plan")
        assert any("missing package scope check" in error for error in pressure_errors)
        assert any("missing networking scope check" in error for error in pressure_errors)
        explicit_pressure_task = generic_pressure_task.replace(
            "Run the focused test with a performance budget and launch budget.",
            "Run the package consumer and package build with explicit cache policy, retry policy, performance budget and launch budget.",
        )
        (plan / "task-001.md").write_text(explicit_pressure_task)
        assert validate_package(repo, adapter, "sample", "sample", "plan") == []
        (package / "design.md").write_text(original_design)
        (package / "verification.md").write_text(original_verification)
        (package / "meta.json").write_text(json.dumps(planned))
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(planned)))
        (plan / "task-001.md").write_text(task)
        (plan / "task-002.md").write_text(task_2)
        (plan / "task-003.md").write_text(task_3)
        invented_scope = dict(planned)
        invented_scope["engineering_scopes"] = ["application", "performance"]
        invented_scope["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/performance-a.md", "TestClient/workflow/performance-b.md",
        ]
        (package / "meta.json").write_text(json.dumps(invented_scope))
        assert any("snapshot" in error for error in validate_package(repo, adapter, "sample", "sample", "implement"))
        removed_scope = dict(planned)
        removed_scope["engineering_scopes"] = ["performance"]
        removed_scope["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/performance-a.md",
            "TestClient/workflow/performance-b.md",
        ]
        (package / "meta.json").write_text(json.dumps(removed_scope))
        assert any("snapshot" in error for error in validate_package(repo, adapter, "sample", "sample", "implement"))
        (package / "meta.json").write_text(json.dumps(planned))
        snapshot_path = plan / "rule-selection.json"; original_snapshot = snapshot_path.read_text()
        tampered_snapshot = json.loads(original_snapshot); tampered_snapshot["fingerprint"] = "0" * 64
        snapshot_path.write_text(json.dumps(tampered_snapshot))
        assert any("tampered" in error for error in validate_package(repo, adapter, "sample", "sample", "implement"))
        snapshot_path.write_text(original_snapshot)
        bad = task.replace("Depends on: none", "Depends on: task-999")
        (plan/"task-001.md").write_text(bad)
        assert validate_package(repo, adapter, "sample", "sample", "plan")
        (plan/"task-001.md").write_text(task)

        source=repo/"TestClient/Sources/Sample.swift"; source.parent.mkdir(parents=True); source.write_text("struct Sample {}\n")
        test_source=repo/"TestClient/Tests/SampleTests.swift"; test_source.parent.mkdir(parents=True); test_source.write_text("final class SampleTests {}\n")
        independent_source=repo/"TestClient/Tests/IndependentTests.swift"; independent_source.write_text("final class IndependentTests {}\n")
        evidence=package/"evidence"; evidence.mkdir(exist_ok=True); (evidence/"task-001.md").write_text("Focused test PASS.\n"); (evidence/"task-002.md").write_text("Integration test PASS.\n"); (evidence/"task-003.md").write_text("Independent test PASS.\n")
        done_task=task.replace("Status: pending", "Status: done").replace("Evidence: none", "Evidence: evidence/task-001.md").replace("proposed:", "existing:")
        done_task_2=task_2.replace("Status: pending", "Status: done").replace("Evidence: none", "Evidence: evidence/task-002.md").replace("proposed:", "existing:")
        done_task_3=task_3.replace("Status: pending", "Status: done").replace("Evidence: none", "Evidence: evidence/task-003.md").replace("proposed:", "existing:")
        (plan/"task-001.md").write_text(done_task)
        (plan/"task-002.md").write_text(done_task_2)
        (plan/"task-003.md").write_text(done_task_3)
        implementing=dict(planned); implementing.update(status="implementing",tasks_done=3)
        (package/"meta.json").write_text(json.dumps(implementing))
        assert validate_package(repo, adapter, "sample", "sample", "implement") == []

        for name in ("req","ac","preq","pac"):(evidence/f"{name}.md").write_text("Current verification PASS.\n")
        failed_verification = (
            "# Verification\n\n" + fixture_modularity_verification("PASS")
            + "\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | FAIL |\n"
        )
        (package/"verification.md").write_text(failed_verification)
        reopened_task=done_task.replace("Status: done", "Status: pending").replace("Evidence: evidence/task-001.md", "Evidence: none")
        reopened_task_2=done_task_2.replace("Status: done", "Status: pending").replace("Evidence: evidence/task-002.md", "Evidence: none")
        reopened_task_3=done_task_3.replace("Status: done", "Status: pending").replace("Evidence: evidence/task-003.md", "Evidence: none")
        (plan/"task-001.md").write_text(reopened_task)
        (plan/"task-002.md").write_text(done_task_2)
        recovery=dict(implementing); recovery.update(tasks_done=0,verification_status="FAIL",problems=["TST-AC-1"],verified_at=None,verification_state=None)
        (package/"meta.json").write_text(json.dumps(recovery))
        assert any("done before dependency" in error for error in validate_package(repo, adapter, "sample", "sample", "implement"))
        (plan/"task-002.md").write_text(reopened_task_2)
        assert any("task-003" in error for error in validate_package(repo, adapter, "sample", "sample", "implement"))
        (plan/"task-003.md").write_text(reopened_task_3)
        assert validate_package(repo, adapter, "sample", "sample", "implement") == []
        (plan/"task-001.md").write_text(done_task)
        pending_verification = re.sub(r"\| (?:PASS|FAIL|UNKNOWN) \|", "| pending |", failed_verification)
        pending_verification = re.sub(r"(?m)^(- (?:Dependency graph|Public API and visibility|Module-level tests|Consumer integration and build|App-shell allowlist):) PASS$", r"\1 pending", pending_verification)
        (package/"verification.md").write_text(pending_verification)
        repair_progress=dict(recovery); repair_progress.update(tasks_done=1,problems=[],verification_status="pending")
        (package/"meta.json").write_text(json.dumps(repair_progress))
        assert validate_package(repo, adapter, "sample", "sample", "implement") == []
        (plan/"task-002.md").write_text(done_task_2)
        repair_mid=dict(repair_progress); repair_mid["tasks_done"]=2
        (package/"meta.json").write_text(json.dumps(repair_mid))
        assert validate_package(repo, adapter, "sample", "sample", "implement") == []
        (plan/"task-003.md").write_text(done_task_3)
        repair_complete=dict(repair_progress); repair_complete["tasks_done"]=3
        (package/"meta.json").write_text(json.dumps(repair_complete))
        assert validate_package(repo, adapter, "sample", "sample", "implement") == []

        passing_verification = failed_verification.replace("| FAIL |", "| PASS |")
        (package/"verification.md").write_text(passing_verification)
        verified=dict(repair_complete); verified.update(status="verified",problems=[],verification_status="PASS",verified_at="2026-07-15T12:00:00Z",verification_state="evidence/verification-state.json")
        visual_rule = repo / "workflow/rules/visual-language.md"
        technical_fingerprint = compute_state(repo, adapter, package, verified)["fingerprint"]
        product_ui_state = dict(verified)
        product_ui_state["engineering_scopes"] = ["application", "ui"]
        product_ui_state["applicable_rule_files"] = [
            "TestClient/workflow/base.md", "TestClient/workflow/application.md",
            "TestClient/workflow/ui.md",
        ]
        product_ui_fingerprint = compute_state(repo, adapter, package, product_ui_state)["fingerprint"]
        visual_rule.write_text("Changed shared semantic visual language contract.\n")
        assert compute_state(repo, adapter, package, verified)["fingerprint"] == technical_fingerprint
        assert compute_state(repo, adapter, package, product_ui_state)["fingerprint"] != product_ui_fingerprint
        visual_rule.write_text("Current shared calm soft-blue semantic visual language contract.\n")
        state=compute_state(repo, adapter, package, verified); state["captured_at"]="2026-07-15T12:00:00Z"
        (evidence/"verification-state.json").write_text(json.dumps(state))
        (package/"meta.json").write_text(json.dumps(verified))
        assert validate_package(repo, adapter, "sample", "sample", "verify") == []
        selected_rule = repo / "TestClient/workflow/application.md"
        selected_rule.write_text("Changed selected application rule.\n")
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        selected_rule.write_text("Current selected application rule.\n")
        ux_artifact.write_text(ux_source + "\nLate native UX decision.\n")
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        ux_artifact.unlink()
        unselected_rule = repo / "TestClient/workflow/performance-a.md"
        unselected_rule.write_text("Changed but still unselected performance rule.\n")
        assert validate_package(repo, adapter, "sample", "sample", "archive") == []
        unselected_rule.write_text("Unselected performance rule A.\n")
        adapter_path = repo / "TestClient/workflow/platform-contract.json"
        adapter["platform_ux"]["design_language"] = "Changed Native UI"
        adapter_path.write_text(json.dumps({key: value for key, value in adapter.items() if key != "_path"}))
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        adapter["platform_ux"]["design_language"] = "Native Test UI"
        adapter["scope_rule_profiles"]["performance"].reverse()
        adapter_path.write_text(json.dumps({key: value for key, value in adapter.items() if key != "_path"}))
        assert validate_package(repo, adapter, "sample", "sample", "archive") == []
        adapter["scope_rule_profiles"]["performance"].reverse()
        adapter["scope_task_checks"]["application"] = ["application boundary"]
        adapter_path.write_text(json.dumps({key: value for key, value in adapter.items() if key != "_path"}))
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        adapter["scope_task_checks"].pop("application")
        adapter["scope_task_checks"]["performance"] = ["performance budget"]
        adapter_path.write_text(json.dumps({key: value for key, value in adapter.items() if key != "_path"}))
        assert validate_package(repo, adapter, "sample", "sample", "archive") == []
        adapter["scope_task_checks"].pop("performance")
        adapter_path.write_text(json.dumps({key: value for key, value in adapter.items() if key != "_path"}))
        verification_path = package/"verification.md"
        verification_path.write_text(passing_verification.replace("PASS |", "UNKNOWN |", 1))
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        verification_path.write_text(passing_verification)
        evidence_req = evidence/"req.md"; evidence_req.write_text("Changed verification evidence.\n")
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        evidence_req.write_text("Current verification PASS.\n")
        extra_evidence = evidence/"extra.md"; extra_evidence.write_text("Late evidence.\n")
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        extra_evidence.unlink()
        source.write_text("struct Sample { let stale = true }\n")
        assert any("stale" in x for x in validate_package(repo, adapter, "sample", "sample", "archive"))
        source.write_text("struct Sample {}\n")
        assert validate_package(repo, adapter, "sample", "sample", "archive") == []
    print("validate-platform-change self-test: PASS (change-aware lifecycle and adversarial gates)")
    return 0


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--platform"); parser.add_argument("--feature"); parser.add_argument("--change")
    parser.add_argument("--mode", choices=("propose","plan","implement","verify","archive"))
    parser.add_argument("--root", type=Path, default=repository_root()); parser.add_argument("--self-test", action="store_true")
    args=parser.parse_args()
    if args.self_test: return self_test()
    if not args.platform or not args.feature or not args.mode: parser.error("--platform, --feature and --mode are required")
    if not SLUG_RE.fullmatch(args.feature): print("BLOCKED: feature must be strict kebab-case; no files were written."); return 3
    if args.change is not None and not SLUG_RE.fullmatch(args.change): print("BLOCKED: change_id must be strict kebab-case; no files were written."); return 3
    repo=args.root.resolve()
    try:
        adapter=load_adapter(repo,args.platform)
        require_capability(adapter, "archive-implementation" if args.mode == "archive" else args.mode)
        change, _package=resolve_change(repo,adapter,args.feature,args.change,args.mode)
        errors=validate_package(repo,adapter,args.feature,change,args.mode)
    except (AdapterError, RuleProfileError) as error:
        print(f"BLOCKED: {error}."); return 4
    if errors:
        print(f"Platform package: INVALID ({len(errors)} blocker)")
        for error in errors: print(f"- {error}")
        return 2
    print(f"Platform package: VALID ({args.mode}, {adapter['platform_name']}/{args.feature}/{change})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
