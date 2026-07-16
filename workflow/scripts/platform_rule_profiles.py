#!/usr/bin/env python3
"""Canonical validation and resolution for platform engineering rule profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import hashlib
import json
import re

PHASES = ("propose", "plan", "implement", "verify")
CAPABILITIES = ("propose", "plan", "implement", "verify", "archive-implementation")
SCOPE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRE_COMMIT_KEYS = {
    "source_suffixes", "generated_globs", "secret_globs",
    "security_sensitive_globs", "ui_globs", "localization_globs",
    "project_globs", "tool_globs",
}
COMMON_MODULARITY_RULE = "workflow/rules/system-design/modularity.md"
CURRENT_MODULARITY_CONTRACT_VERSION = 1
LEGACY_MODULARITY_CONTRACT_VERSION = 0
LEGACY_REGISTRY_PATH = "workflow/compatibility/modularity-v0.json"
LEGACY_REGISTRY_CANONICAL_SHA256 = "6a8bbda66f53fdf2b0a8dbe2986d394133f0eec98a63ba047df5e6908c45a47a"
LEGACY_REGISTRY_IDENTITIES = (
    ("iOS", "client-bootstrap", "initial-scaffold", "iOS/specs/client-bootstrap/changes/initial-scaffold"),
    ("Android", "client-bootstrap", "initial-scaffold", "Android/specs/client-bootstrap/changes/initial-scaffold"),
)
LEGACY_META_MUTABLE_FIELDS = {
    "status", "tasks_done", "problems", "verification_status", "verified_at",
    "verification_state",
}
LEGACY_META_EXACT_FIELDS = {
    "platform", "feature", "change_id", "change_type", "tier", "status",
    "shared_product_spec", "product_status", "product_approval",
    "product_impact", "impact_evidence", "engineering_scopes",
    "applicable_rule_files", "rule_selection_snapshot", "blocking_questions",
    "problems", "design_gate", "tasks_total", "tasks_done",
    "verification_status", "verified_at", "verification_state",
}
LEGACY_META_IDENTITY_FIELDS = tuple(
    sorted(LEGACY_META_EXACT_FIELDS - LEGACY_META_MUTABLE_FIELDS)
)
LEGACY_HASH_KEYS = {
    "design_sha256", "meta_identity_sha256", "rule_selection_sha256",
    "plan_readme_sha256", "task_graph_sha256",
}
MODULARITY_KEYS = {
    "contract_version", "isolation_scope", "platform_rule", "physical_units",
    "legacy_task_checks",
}


class RuleProfileError(ValueError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return _sha256_bytes(encoded)


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise RuleProfileError(f"legacy modularity anchor requires regular {label}")
    return path


def legacy_meta_identity_projection(meta: dict[str, object]) -> dict[str, object]:
    if set(meta) != LEGACY_META_EXACT_FIELDS:
        missing = sorted(LEGACY_META_EXACT_FIELDS - set(meta))
        extra = sorted(set(meta) - LEGACY_META_EXACT_FIELDS)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("unexpected: " + ", ".join(extra))
        raise RuleProfileError(
            "legacy modularity meta must use the exact historical key set ("
            + "; ".join(details) + ")"
        )
    return {field: meta[field] for field in LEGACY_META_IDENTITY_FIELDS}


def normalized_legacy_task(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(?m)^(- Status:)\s*.*$", r"\1 <lifecycle>", normalized)
    normalized = re.sub(r"(?m)^(- Evidence:)\s*.*$", r"\1 <lifecycle>", normalized)
    return normalized


def legacy_package_hashes(package: Path, meta: dict[str, object]) -> dict[str, str]:
    design = _regular_file(package / "design.md", "design.md")
    selection = _regular_file(package / "plan/rule-selection.json", "plan/rule-selection.json")
    plan_readme = _regular_file(package / "plan/README.md", "plan/README.md")
    plan = package / "plan"
    if plan.is_symlink() or not plan.is_dir():
        raise RuleProfileError("legacy modularity anchor requires regular plan directory")
    tasks = sorted(plan.glob("task-*.md"), key=lambda item: item.name)
    if (
        not tasks
        or any(not re.fullmatch(r"task-[0-9]{3}\.md", task.name) for task in tasks)
        or any(task.is_symlink() or not task.is_file() for task in tasks)
    ):
        raise RuleProfileError("legacy modularity task graph requires sorted regular task-NNN.md files")
    task_graph = [
        {
            "file": task.name,
            "normalized_sha256": _sha256_bytes(
                normalized_legacy_task(task.read_text(encoding="utf-8")).encode()
            ),
        }
        for task in tasks
    ]
    return {
        "design_sha256": _sha256_bytes(design.read_bytes()),
        "meta_identity_sha256": _canonical_hash(legacy_meta_identity_projection(meta)),
        "rule_selection_sha256": _sha256_bytes(selection.read_bytes()),
        "plan_readme_sha256": _sha256_bytes(plan_readme.read_bytes()),
        "task_graph_sha256": _canonical_hash(task_graph),
    }


def load_legacy_registry(repo: Path) -> list[dict[str, object]]:
    path = repo / LEGACY_REGISTRY_PATH
    if path.is_symlink() or not path.is_file():
        raise RuleProfileError(f"legacy modularity registry is missing: {LEGACY_REGISTRY_PATH}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuleProfileError(f"legacy modularity registry JSON is invalid: {error}") from error
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "task_normalization", "packages"}:
        raise RuleProfileError("legacy modularity registry must use the exact canonical schema")
    if _canonical_hash(raw) != LEGACY_REGISTRY_CANONICAL_SHA256:
        raise RuleProfileError(
            "legacy modularity registry differs from the code-pinned canonical trust anchor"
        )
    if raw.get("schema_version") != 1:
        raise RuleProfileError("legacy modularity registry schema_version must be 1")
    if raw.get("task_normalization") != {"ignored_field_values": ["Status", "Evidence"]}:
        raise RuleProfileError("legacy modularity registry task normalization must ignore only Status/Evidence values")
    packages = raw.get("packages")
    if not isinstance(packages, list):
        raise RuleProfileError("legacy modularity registry packages must be an array")
    identities: set[tuple[str, str, str]] = set()
    for entry in packages:
        if not isinstance(entry, dict) or set(entry) != {"platform", "feature", "change_id", "package_path", "hashes"}:
            raise RuleProfileError("legacy modularity registry entry must use the exact canonical schema")
        platform = entry.get("platform")
        feature = entry.get("feature")
        change = entry.get("change_id")
        package_path = entry.get("package_path")
        if (
            not isinstance(platform, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", platform)
            or not isinstance(feature, str) or not SCOPE_RE.fullmatch(feature)
            or not isinstance(change, str) or not SCOPE_RE.fullmatch(change)
            or not isinstance(package_path, str)
        ):
            raise RuleProfileError("legacy modularity registry identity is invalid")
        value = Path(package_path)
        expected = f"{platform}/specs/{feature}/changes/{change}"
        if value.is_absolute() or ".." in value.parts or value.as_posix() != expected:
            raise RuleProfileError("legacy modularity registry package_path must exactly match identity")
        identity = (platform, feature, change)
        if identity in identities:
            raise RuleProfileError("legacy modularity registry identities must be unique")
        identities.add(identity)
        hashes = entry.get("hashes")
        if (
            not isinstance(hashes, dict) or set(hashes) != LEGACY_HASH_KEYS
            or not all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values())
        ):
            raise RuleProfileError("legacy modularity registry hashes must use the exact sha256 schema")
    actual_identities = tuple(
        (
            str(entry["platform"]), str(entry["feature"]), str(entry["change_id"]),
            str(entry["package_path"]),
        )
        for entry in packages
    )
    if actual_identities != LEGACY_REGISTRY_IDENTITIES:
        raise RuleProfileError("legacy modularity registry must contain only the code-pinned identities in canonical order")
    return packages


def resolve_package_contract_version(
    repo: Path, adapter: dict[str, object], meta: dict[str, object], package: Path,
    mode: str | None = None,
) -> int:
    raw = meta.get("modularity_contract_version")
    if raw is not None:
        version = validate_contract_version(raw)
    else:
        version = LEGACY_MODULARITY_CONTRACT_VERSION
    if version == CURRENT_MODULARITY_CONTRACT_VERSION:
        return version
    snapshot = package / "plan/rule-selection.json"
    if (
        meta.get("status") not in {"planned", "implementing", "verified"}
        or meta.get("rule_selection_snapshot") != "plan/rule-selection.json"
        or snapshot.is_symlink() or not snapshot.is_file()
    ):
        raise RuleProfileError("legacy modularity contract requires a sealed planned/implementing/verified package")
    if mode in {"propose", "plan"}:
        raise RuleProfileError("legacy modularity contract cannot run Propose or Plan; migrate through a new change package")
    identity = (meta.get("platform"), meta.get("feature"), meta.get("change_id"))
    matches = [
        entry for entry in load_legacy_registry(repo)
        if (entry["platform"], entry["feature"], entry["change_id"]) == identity
    ]
    if len(matches) != 1:
        raise RuleProfileError("legacy modularity package identity is not registered")
    entry = matches[0]
    expected_package = (repo / str(entry["package_path"])).resolve()
    if package.resolve() != expected_package or package.is_symlink() or not package.is_dir():
        raise RuleProfileError("legacy modularity package path does not match registry identity")
    actual_hashes = legacy_package_hashes(package, meta)
    if actual_hashes != entry["hashes"]:
        mismatches = sorted(
            key for key in LEGACY_HASH_KEYS if actual_hashes.get(key) != entry["hashes"].get(key)
        )
        raise RuleProfileError(
            "legacy modularity package differs from registered immutable structure: "
            + ", ".join(mismatches)
        )
    return version


def validate_capabilities(adapter: dict[str, object]) -> list[str]:
    raw = adapter.get("lifecycle_capabilities")
    if not isinstance(raw, list) or not raw or raw != [item for item in CAPABILITIES if item in raw]:
        raise RuleProfileError("lifecycle_capabilities must be a non-empty canonical ordered subset")
    required = {"plan": "propose", "implement": "plan", "verify": "implement", "archive-implementation": "verify"}
    for capability, dependency in required.items():
        if capability in raw and dependency not in raw:
            raise RuleProfileError(f"lifecycle capability {capability} requires {dependency}")
    return raw


def require_capability(adapter: dict[str, object], capability: str) -> None:
    capabilities = validate_capabilities(adapter)
    if capability not in capabilities:
        raise RuleProfileError(f"NOT IMPLEMENTED: platform capability '{capability}' is unavailable; no files were written")


def _safe_glob(raw: object) -> bool:
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
        return False
    return re.fullmatch(r"[A-Za-z0-9_./*?+-]+", raw) is not None


def validate_pre_commit_profile(adapter: dict[str, object]) -> dict[str, object]:
    profile = adapter.get("pre_commit")
    if not isinstance(profile, dict) or set(profile) != PRE_COMMIT_KEYS:
        raise RuleProfileError("pre_commit must contain the exact canonical schema keys")
    suffixes = profile["source_suffixes"]
    if (
        not isinstance(suffixes, list) or not suffixes
        or len(suffixes) != len(set(suffixes))
        or not all(isinstance(item, str) and re.fullmatch(r"\.[a-z0-9]+", item) for item in suffixes)
    ):
        raise RuleProfileError("pre_commit.source_suffixes must be a sorted unique extension list")
    for key in PRE_COMMIT_KEYS - {"source_suffixes", "tool_globs"}:
        values = profile[key]
        if not isinstance(values, list) or not values or len(values) != len(set(values)) or not all(_safe_glob(item) for item in values):
            raise RuleProfileError(f"pre_commit.{key} must be a unique non-empty safe glob list")
    tools = profile["tool_globs"]
    if not isinstance(tools, dict) or not tools:
        raise RuleProfileError("pre_commit.tool_globs must be a non-empty object")
    for tool, globs in tools.items():
        if not isinstance(tool, str) or not SCOPE_RE.fullmatch(tool):
            raise RuleProfileError(f"invalid pre_commit tool name: {tool}")
        if not isinstance(globs, list) or not globs or len(globs) != len(set(globs)) or not all(_safe_glob(item) for item in globs):
            raise RuleProfileError(f"pre_commit.tool_globs.{tool} must be a unique non-empty safe glob list")
    return profile


def _safe_rule(repo: Path, raw: object, label: str, require_files: bool) -> str:
    if not isinstance(raw, str) or not raw:
        raise RuleProfileError(f"{label} entries must be non-empty strings")
    value = Path(raw)
    if value.is_absolute() or ".." in value.parts or value.suffix != ".md":
        raise RuleProfileError(f"{label} contains unsafe rule path: {raw}")
    resolved = (repo / value).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError as error:
        raise RuleProfileError(f"{label} rule escapes repository: {raw}") from error
    if require_files and not resolved.is_file():
        raise RuleProfileError(f"{label} rule does not exist: {raw}")
    return value.as_posix()


def _rule_list(repo: Path, value: object, label: str, require_files: bool) -> list[str]:
    if not isinstance(value, list) or not value:
        raise RuleProfileError(f"{label} must be a non-empty list")
    rules = [_safe_rule(repo, item, label, require_files) for item in value]
    if len(rules) != len(set(rules)):
        raise RuleProfileError(f"{label} contains duplicate rules")
    return rules


def validate_modularity_config(
    adapter: dict[str, object], catalog: list[str], scopes: dict[str, list[str]]
) -> dict[str, object]:
    config = adapter.get("modularity")
    if not isinstance(config, dict) or set(config) != MODULARITY_KEYS:
        raise RuleProfileError("modularity must contain the exact canonical schema keys")
    if config.get("contract_version") != CURRENT_MODULARITY_CONTRACT_VERSION:
        raise RuleProfileError("modularity.contract_version must equal the current supported version")
    isolation_scope = config.get("isolation_scope")
    if not isinstance(isolation_scope, str) or isolation_scope not in scopes:
        raise RuleProfileError("modularity.isolation_scope must be a known engineering scope")
    platform_rule = config.get("platform_rule")
    platform_root = str(adapter.get("platform_root", "")).rstrip("/")
    if (
        not isinstance(platform_rule, str)
        or platform_rule not in catalog
        or not platform_root
        or not platform_rule.startswith(f"{platform_root}/")
    ):
        raise RuleProfileError("modularity.platform_rule must be a catalogued platform-owned rule")
    physical_units = config.get("physical_units")
    if (
        not isinstance(physical_units, list) or not physical_units
        or len(physical_units) != len(set(physical_units))
        or not all(
            isinstance(item, str) and len(item.strip()) >= 3
            and not re.search(r"<[^>]+>|\b(?:TODO|TBD)\b", item, re.IGNORECASE)
            for item in physical_units
        )
    ):
        raise RuleProfileError("modularity.physical_units must be a unique substantive list")
    if any(re.search(r"(?<!non-)\b(?:app|application)\b.*\b(?:target|module)\b", item, re.IGNORECASE) for item in physical_units):
        raise RuleProfileError("modularity.physical_units must be non-application units")
    legacy_checks = config.get("legacy_task_checks")
    if (
        not isinstance(legacy_checks, list) or not legacy_checks
        or len(legacy_checks) != len(set(legacy_checks))
        or not all(isinstance(item, str) and item.strip() for item in legacy_checks)
    ):
        raise RuleProfileError("modularity.legacy_task_checks must preserve the v0 isolation-scope checks")
    return config


def validate_contract_version(value: object) -> int:
    if isinstance(value, bool) or value not in {
        LEGACY_MODULARITY_CONTRACT_VERSION, CURRENT_MODULARITY_CONTRACT_VERSION,
    }:
        raise RuleProfileError("unsupported modularity_contract_version")
    return int(value)


def phase_profiles_for_version(
    adapter: dict[str, object], phases: dict[str, list[str]], contract_version: int
) -> dict[str, list[str]]:
    version = validate_contract_version(contract_version)
    if version == CURRENT_MODULARITY_CONTRACT_VERSION:
        return {phase: list(rules) for phase, rules in phases.items()}
    config = adapter["modularity"]
    removed = {COMMON_MODULARITY_RULE, str(config["platform_rule"])}
    return {
        phase: [rule for rule in rules if rule not in removed]
        for phase, rules in phases.items()
    }


def scope_task_checks_for_version(
    adapter: dict[str, object], scope: str, contract_version: int
) -> list[str]:
    version = validate_contract_version(contract_version)
    config = adapter["modularity"]
    if version == LEGACY_MODULARITY_CONTRACT_VERSION and scope == config["isolation_scope"]:
        return list(config["legacy_task_checks"])
    return list(adapter.get("scope_task_checks", {}).get(scope, []))


def validate_profiles(
    repo: Path, adapter: dict[str, object], require_files: bool = True
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    catalog = _rule_list(repo, adapter.get("rule_files"), "rule_files", require_files)
    capabilities = validate_capabilities(adapter)
    supported_phases = [phase for phase in PHASES if phase in capabilities]
    phase_value = adapter.get("phase_rule_profiles")
    if not isinstance(phase_value, dict) or list(phase_value) != supported_phases:
        raise RuleProfileError("phase_rule_profiles must exactly match supported engineering capabilities in canonical order")
    phases = {
        phase: _rule_list(repo, phase_value[phase], f"phase_rule_profiles.{phase}", require_files)
        for phase in supported_phases
    }
    scope_value = adapter.get("scope_rule_profiles")
    if not isinstance(scope_value, dict) or not scope_value:
        raise RuleProfileError("scope_rule_profiles must be a non-empty object")
    scopes: dict[str, list[str]] = {}
    for scope, rules in scope_value.items():
        if not isinstance(scope, str) or not SCOPE_RE.fullmatch(scope):
            raise RuleProfileError(f"invalid engineering scope: {scope}")
        scopes[scope] = _rule_list(repo, rules, f"scope_rule_profiles.{scope}", require_files)
    validate_modularity_config(adapter, catalog, scopes)
    dependencies = adapter.get("scope_dependencies", {})
    if not isinstance(dependencies, dict) or set(dependencies) - set(scopes):
        raise RuleProfileError("scope_dependencies keys must be known engineering scopes")
    for scope, required_scopes in dependencies.items():
        if (
            not isinstance(required_scopes, list) or not required_scopes
            or required_scopes != sorted(set(required_scopes))
            or not all(isinstance(item, str) and item in scopes and item != scope for item in required_scopes)
        ):
            raise RuleProfileError(f"scope_dependencies.{scope} must be a sorted unique list of other known scopes")
    profiled = {rule for rules in phases.values() for rule in rules}
    profiled.update(rule for rules in scopes.values() for rule in rules)
    unknown = sorted(profiled - set(catalog))
    unused = sorted(set(catalog) - profiled)
    if unknown:
        raise RuleProfileError(f"profile rules missing from rule_files catalog: {', '.join(unknown)}")
    if unused:
        raise RuleProfileError(f"rule_files entries are not assigned to a profile: {', '.join(unused)}")
    return catalog, phases, scopes


def validate_scope_dependencies(
    adapter: dict[str, object], selected: list[str]
) -> None:
    dependencies = adapter.get("scope_dependencies", {})
    selected_set = set(selected)
    for scope in selected:
        missing = set(dependencies.get(scope, [])) - selected_set
        if missing:
            raise RuleProfileError(
                f"engineering scope {scope} requires scopes: {', '.join(sorted(missing))}"
            )


def normalize_scopes(raw_scopes: Iterable[object], known: dict[str, list[str]]) -> list[str]:
    scopes: list[str] = []
    for raw in raw_scopes:
        if not isinstance(raw, str) or raw not in known:
            raise RuleProfileError(f"unknown engineering scope: {raw}")
        if raw not in scopes:
            scopes.append(raw)
    return sorted(scopes)


def _ordered_union(groups: Iterable[Iterable[str]]) -> list[str]:
    result: list[str] = []
    for group in groups:
        for rule in group:
            if rule not in result:
                result.append(rule)
    return result


def rules_for_phase(
    repo: Path, adapter: dict[str, object], phase: str, raw_scopes: Iterable[object],
    require_files: bool = True,
    contract_version: int = CURRENT_MODULARITY_CONTRACT_VERSION,
) -> tuple[list[str], list[str]]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter, require_files)
    if phase not in PHASES:
        raise RuleProfileError(f"unknown lifecycle phase: {phase}")
    require_capability(adapter, phase)
    phases = phase_profiles_for_version(adapter, phases, contract_version)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    validate_scope_dependencies(adapter, scopes)
    return scopes, _ordered_union([phases[phase], *(scope_profiles[scope] for scope in scopes)])


def applicable_rules(
    repo: Path, adapter: dict[str, object], raw_scopes: Iterable[object],
    require_files: bool = True,
    contract_version: int = CURRENT_MODULARITY_CONTRACT_VERSION,
) -> tuple[list[str], list[str]]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter, require_files)
    phases = phase_profiles_for_version(adapter, phases, contract_version)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    validate_scope_dependencies(adapter, scopes)
    groups = [phases[phase] for phase in PHASES if phase in phases]
    groups.extend(scope_profiles[scope] for scope in scopes)
    return scopes, _ordered_union(groups)


def semantic_projection(
    repo: Path, adapter: dict[str, object], raw_scopes: Iterable[object],
    contract_version: int = CURRENT_MODULARITY_CONTRACT_VERSION,
) -> dict[str, object]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter)
    version = validate_contract_version(contract_version)
    phases = phase_profiles_for_version(adapter, phases, version)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    validate_scope_dependencies(adapter, scopes)
    identity_fields = (
        "platform_input", "platform_name", "platform_root", "package_root",
        "active_changes_namespace", "archive_namespace", "production_roots",
        "protected_roots", "production_exclusions", "contract_prefix",
        "boundary_guard", "extended_design_sections", "context_file_suffixes",
        "context_excluded_directories", "context_always_include_globs",
    )
    contract = {
            **{field: adapter[field] for field in identity_fields},
            "lifecycle_capabilities": validate_capabilities(adapter),
            "platform_ux": adapter.get("platform_ux"),
    }
    if version == CURRENT_MODULARITY_CONTRACT_VERSION:
        contract["modularity"] = adapter.get("modularity")
    return {
        "contract": contract,
        "phase_rule_profiles": {phase: phases[phase] for phase in PHASES if phase in phases},
        "scope_rule_profiles": {scope: scope_profiles[scope] for scope in scopes},
        "scope_task_checks": {
            scope: scope_task_checks_for_version(adapter, scope, version) for scope in scopes
        },
        "scope_dependencies": {
            scope: adapter.get("scope_dependencies", {}).get(scope, []) for scope in scopes
            if scope in adapter.get("scope_dependencies", {})
        },
    }
