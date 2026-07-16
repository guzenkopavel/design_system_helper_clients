#!/usr/bin/env python3
"""Fail-closed validator for adapter-backed platform change packages."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path

from platform_rule_profiles import (
    RuleProfileError,
    applicable_rules,
    semantic_projection,
    require_capability,
    validate_capabilities,
    validate_pre_commit_profile,
    validate_profiles,
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_RE = re.compile(r"^task-\d{3}$")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|<[^>\n]+>|\{\{|\}\}|\.\.\.", re.I)
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
}
COMMON_DESIGN = (
    "Current context", "Proposed architecture and boundaries",
    "Data and control flow", "Error and recovery model", "Verification strategy",
)
TERMINAL_MODES = {"verify", "archive"}
PLATFORM_UX_KEYS = {"role", "artifact", "design_language", "required_terms", "task_checks"}
PLATFORM_UX_HEADINGS = (
    "Evidence inspected", "Shared intent mapping",
    "Information architecture and navigation", "Component and state mapping",
    "Native visual language", "Color roles and appearance",
    "Accessibility and localization", "Motion and interaction",
    "Device and layout adaptation", "Fallback and availability",
    "Verification scenarios", "Open gaps",
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
            active = active_change_ids(repo, adapter, feature)
            if len(active) != 1:
                raise AdapterError(
                    f"omitted --change requires exactly one active package; found {len(active)}"
                )
            change = active[0]
    if not SLUG_RE.fullmatch(change):
        raise AdapterError("change_id must be a strict kebab-case slug")
    root = changes_root(repo, adapter, feature).resolve()
    package = (root / change).resolve()
    if package.parent != root or not is_subpath(package, root):
        raise AdapterError("change_id escapes active package root")
    return change, package


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


def explicit_none(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = re.sub(r"[`*_#|>\-]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".!;: ").casefold()
    return cleaned in {"none", "no open questions", "нет открытых вопросов"}


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^-\s*\**{re.escape(label)}\s*:\**\s*`?([^`\n]+)`?\s*$", text)
    return match.group(1).strip() if match else None


def rule_selection_snapshot(meta: dict[str, object]) -> dict[str, object]:
    selection = {
        "engineering_scopes": meta.get("engineering_scopes"),
        "applicable_rule_files": meta.get("applicable_rule_files"),
    }
    encoded = json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
    return {"schema_version": 1, **selection, "fingerprint": hashlib.sha256(encoded).hexdigest()}


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


def parse_tasks(repo: Path, package: Path) -> tuple[list[dict[str, object]], list[str]]:
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
        for name in ("Layer", "Engineering scopes", "Depends on", "Status", "Evidence", "Estimate (ideal)", "Paths"):
            match = re.search(rf"(?mi)^-\s*{re.escape(name)}:\s*(.+)$", body)
            if match:
                fields[name] = match.group(1).strip()
            else:
                errors.append(f"{path.name} missing {name}")
        for name in ("Goal", "Inline contract context", "Steps", "Verification", "Expected result", "Out of scope"):
            if not substantive(section(body, name), 12):
                errors.append(f"{path.name} missing substantive section: {name}")
        layer = fields.get("Layer", "").casefold()
        if layer not in {"domain", "data", "presentation", "infrastructure", "tests"}:
            errors.append(f"{path.name} must declare one allowed Layer")
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
        raw_deps = fields.get("Depends on", "")
        deps = set() if raw_deps.casefold() in {"none", "-", "—"} else set(re.findall(r"\btask-\d{3}\b", raw_deps))
        if raw_deps.casefold() not in {"none", "-", "—"} and not deps:
            errors.append(f"{path.name} invalid dependencies")
        for dep in deps - task_ids:
            errors.append(f"{path.name} depends on missing {dep}")
        if path.stem in deps:
            errors.append(f"{path.name} depends on itself")
        tasks.append({"id": path.stem, "path": path, "body": body, "layer": layer, "engineering_scopes": task_scopes, "status": status, "evidence": evidence, "deps": deps, "paths": parsed_paths})
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
    projection = semantic_projection(repo, adapter, meta.get("engineering_scopes", []))
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
    missing = sorted(REQUIRED_META - set(meta))
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
            normalized_scopes, expected_rules = applicable_rules(repo, adapter, raw_scopes)
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
    if not isinstance(meta.get("problems"), list):
        errors.append("problems must be an array")
    elif not all(isinstance(item, str) for item in meta.get("problems", [])):
        errors.append("problems entries must be contract ID strings")

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

    package_scopes = set(raw_scopes) if isinstance(raw_scopes, list) else set()
    platform_ux_errors = validate_platform_ux(repo, adapter, package, feature, meta, package_scopes)
    errors.extend(platform_ux_errors)
    if platform_ux_errors and meta.get("design_gate") == "PASS":
        errors.append("design_gate cannot PASS without READY platform UX")

    required_files = ("proposal.md", "implementation-spec.md", "design.md", "verification.md")
    for name in required_files:
        if not (package / name).is_file(): errors.append(f"missing {name}")
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
    if meta.get("change_type") == "product-backed" and "ui" in package_scopes:
        if not substantive(section(verification, "Native UX verification"), 20):
            errors.append("verification.md requires Native UX verification")
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

    if mode == "propose":
        if meta.get("problems") != []: errors.append("propose requires empty problems")
        if any(status.casefold() != "pending" for status in row_status.values()): errors.append("propose verification rows must be pending")
        if meta.get("status") != "specified": errors.append("propose requires specified status")
        if meta.get("tasks_total") != 0 or meta.get("tasks_done") != 0: errors.append("specified package task counts must be zero")
        if meta.get("verification_status") != "pending" or meta.get("verified_at") is not None or meta.get("verification_state") is not None: errors.append("specified verification fields must be pending/null")
        return errors

    tasks, task_errors = parse_tasks(repo, package); errors.extend(task_errors)
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
            for check in adapter["scope_task_checks"].get(scope, []):
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
        if any(status.casefold() != "pending" for status in row_status.values()): errors.append("plan verification rows must be pending")
        if meta.get("status") != "planned": errors.append("plan requires planned status")
        if done: errors.append("new plan tasks must all be pending")
        if meta.get("verification_status") != "pending": errors.append("plan verification must be pending")
    elif mode == "implement":
        if meta.get("status") not in {"planned", "implementing"}: errors.append("implement requires planned or implementing status")
        verification_status = meta.get("verification_status")
        problems = [item for item in meta.get("problems", []) if isinstance(item, str)] if isinstance(meta.get("problems"), list) else []
        if verification_status == "pending":
            if problems: errors.append("initial implement state requires empty problems")
            if any(status.casefold() != "pending" for status in row_status.values()): errors.append("initial implement verification rows must be pending")
            if meta.get("verified_at") is not None or meta.get("verification_state") is not None: errors.append("initial implement verification timestamp/state must be null")
        elif verification_status in {"FAIL", "UNKNOWN"}:
            if meta.get("status") != "implementing": errors.append("recovery state requires implementing status")
            if meta.get("verified_at") is not None or meta.get("verification_state") is not None: errors.append("recovery verified_at/state must be null")
            if any(status not in {"PASS", "FAIL", "UNKNOWN"} for status in row_status.values()): errors.append("recovery rows must be exact PASS/FAIL/UNKNOWN")
            non_pass = {contract for contract, status in row_status.items() if status in {"FAIL", "UNKNOWN"}}
            if not non_pass: errors.append("recovery state requires at least one FAIL/UNKNOWN row")
            expected_status = "FAIL" if any(row_status.get(contract) == "FAIL" for contract in non_pass) else "UNKNOWN"
            if verification_status != expected_status: errors.append("recovery verification_status does not match row precedence")
            if set(problems) != non_pass or len(problems) != len(non_pass): errors.append("recovery problems must exactly equal non-PASS contract IDs")
            direct_affected: set[str] = set()
            for contract in non_pass:
                mapped = [task for task in tasks if contract in task_context_ids.get(str(task["id"]), set())]
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
    (product.parent / "brief.md").write_text("Substantive shared product fixture brief.\n", encoding="utf-8")
    (product.parent / "ux.md").write_text("Shared calm soft-blue UX intent for both clients.\n", encoding="utf-8")
    product.write_text(product_validator.fixture_spec(), encoding="utf-8")
    product_validator.write_fixture_receipt(repo, "sample")
    product.write_text(product.read_text(encoding="utf-8").replace("`DRAFT`", "`READY`", 1), encoding="utf-8")
    fixture_product_errors = product_validator.check_product(repo, "sample")
    if fixture_product_errors:
        raise AssertionError(fixture_product_errors)
    package = repo / "TestClient/specs/sample/changes/sample"; package.mkdir(parents=True)
    meta = {"platform":"TestClient","feature":"sample","change_id":"sample","change_type":"product-backed","tier":"standard","status":"specified","shared_product_spec":"specs/product/sample/spec.md","product_status":"READY","product_approval":"APPROVED","product_impact":"PRESENT","impact_evidence":"approved shared behavior applies","engineering_scopes":["application"],"applicable_rule_files":["TestClient/workflow/base.md","TestClient/workflow/application.md"],"rule_selection_snapshot":None,"blocking_questions":[],"problems":[],"design_gate":"PASS","tasks_total":0,"tasks_done":0,"verification_status":"pending","verified_at":None,"verification_state":None}
    (package/"meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (package/"proposal.md").write_text("# Proposal\n\n## Intake\nApproved shared product contract is the implementation intake.\n\n## Goal\nDeliver the selected behavior within the platform boundary.\n\n## Scope\nTyped platform implementation and focused verification are included.\n\n## Engineering scope selection\nApplication scope is selected from discovered production ownership.\n\n## Applicable rule files\nExact lifecycle union includes the base and selected application rules.\n\n## Non-goals\nOther platforms and unrelated cleanup remain outside this change.\n\n## Accepted decisions\nUse adapter ownership and preserve the approved shared behavior.\n\n## Open questions\nNone.\n\n## Risks\nGreenfield integration requires focused boundary verification.\n", encoding="utf-8")
    (package/"implementation-spec.md").write_text("# Spec\n\n## Intake reference\nApproved shared contract applies to this platform change.\n\n## Shared contract references\nReferences REQ-1 and AC-1 without copying behavior text.\n\n## Platform requirements\n### TST-REQ-1 — Boundary\nA typed boundary isolates platform integration and supports focused verification.\n\n## Platform acceptance criteria\n### TST-AC-1 — Boundary result\nA focused test observes the typed boundary returning a deterministic result.\nCovers: TST-REQ-1\n\n## Constraints\nPreserve shared behavior and adapter ownership boundaries.\n\n## Integration points\nConnect through the discovered platform composition boundary.\n\n## Open questions\nNone.\n", encoding="utf-8")
    (package/"design.md").write_text("# Design\n\n## Current context\nThe platform change is greenfield and uses only discovered integration boundaries.\n\n## Proposed architecture and boundaries\nA typed feature boundary separates domain behavior from platform integration details.\n\n## Data and control flow\nInput crosses the domain boundary and a typed result returns to the caller.\n\n## Error and recovery model\nExplicit errors preserve deterministic recovery and prevent hidden retry behavior.\n\n## Applied engineering scopes\n- application: Typed application boundaries and deterministic tests apply to this change.\n\n## Verification strategy\nFocused tests verify the domain boundary and current realized integration path.\n", encoding="utf-8")
    (package/"verification.md").write_text("# Verification\n\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | approval record | pending |\n| AC-1 | integration | Run shared scenario | scenario report | pending |\n| TST-REQ-1 | design | Review current boundary | review record | pending |\n| TST-AC-1 | unit | Run focused boundary test | test report | pending |\n", encoding="utf-8")
    return load_adapter(repo, "test-client"), package, meta


def self_test() -> int:
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
        assert validate_package(repo, adapter, "sample", "sample", "propose") == []
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
            impact_evidence="Repository-only infrastructure has no observable product behavior impact.",
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
        (other/"meta.json").unlink(); other.rmdir()

        plan = package/"plan"; plan.mkdir()
        (plan/"README.md").write_text("# Plan\n\n## Planning frame\nImplement three bounded tasks after approved specification.\n\n## Revalidated engineering scopes and exact rules\n- Engineering scopes: [\"application\"]\n- Applicable rule files: [\"TestClient/workflow/base.md\", \"TestClient/workflow/application.md\"]\n\n## DAG\ntask-001 precedes dependent task-002; task-003 is independent.\n\n## Estimates and multipliers\nThe estimate includes greenfield integration uncertainty.\n\n## Verification strategy\nRun focused boundary and integration tests.\n")
        task = "# task-001\n- Layer: domain\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Sources/Sample.swift\n\n## Goal\nCreate the typed platform behavior boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes its deterministic result.\n\n## Steps\nImplement the typed boundary and its focused behavior test.\n\n## Verification\nRun the focused deterministic boundary test.\n\n## Expected result\nThe boundary returns the expected typed result.\n\n## Out of scope\nOther features and unrelated platform cleanup remain excluded.\n"
        task_2 = "# task-002\n- Layer: tests\n- Engineering scopes: [\"application\"]\n- Depends on: task-001\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Tests/SampleTests.swift\n\n## Goal\nVerify the dependent shared behavior integration.\n\n## Inline contract context\nREQ-1 defines shared behavior and AC-1 observes the integrated result.\n\n## Steps\nAdd the dependent integration scenario after the boundary task.\n\n## Verification\nRun the focused shared integration test.\n\n## Expected result\nThe dependent integration test records the expected result.\n\n## Out of scope\nPlatform boundary changes remain owned by task-001.\n"
        task_3 = "# task-003\n- Layer: tests\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Tests/IndependentTests.swift\n\n## Goal\nVerify an independent owner of the platform acceptance criterion.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the independent result.\n\n## Steps\nAdd the independent focused acceptance scenario.\n\n## Verification\nRun the independent deterministic acceptance test.\n\n## Expected result\nThe independent test records the expected boundary result.\n\n## Out of scope\nDependent integration remains owned by task-002.\n"
        (plan/"task-001.md").write_text(task)
        (plan/"task-002.md").write_text(task_2)
        (plan/"task-003.md").write_text(task_3)
        planned=dict(meta); planned.update(status="planned",tasks_total=3,rule_selection_snapshot="plan/rule-selection.json")
        (plan / "rule-selection.json").write_text(json.dumps(rule_selection_snapshot(planned)))
        (package/"meta.json").write_text(json.dumps(planned))
        assert validate_package(repo, adapter, "sample", "sample", "plan") == []
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
        evidence=package/"evidence"; evidence.mkdir(); (evidence/"task-001.md").write_text("Focused test PASS.\n"); (evidence/"task-002.md").write_text("Integration test PASS.\n"); (evidence/"task-003.md").write_text("Independent test PASS.\n")
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
        failed_verification = "# Verification\n\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | FAIL |\n"
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
