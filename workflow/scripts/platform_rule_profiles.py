#!/usr/bin/env python3
"""Canonical validation and resolution for platform engineering rule profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re

PHASES = ("propose", "plan", "implement", "verify")
CAPABILITIES = ("propose", "plan", "implement", "verify", "archive-implementation")
SCOPE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRE_COMMIT_KEYS = {
    "source_suffixes", "generated_globs", "secret_globs",
    "security_sensitive_globs", "ui_globs", "localization_globs",
    "project_globs", "tool_globs",
}


class RuleProfileError(ValueError):
    pass


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
) -> tuple[list[str], list[str]]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter, require_files)
    if phase not in PHASES:
        raise RuleProfileError(f"unknown lifecycle phase: {phase}")
    require_capability(adapter, phase)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    validate_scope_dependencies(adapter, scopes)
    return scopes, _ordered_union([phases[phase], *(scope_profiles[scope] for scope in scopes)])


def applicable_rules(
    repo: Path, adapter: dict[str, object], raw_scopes: Iterable[object],
    require_files: bool = True,
) -> tuple[list[str], list[str]]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter, require_files)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    validate_scope_dependencies(adapter, scopes)
    groups = [phases[phase] for phase in PHASES if phase in phases]
    groups.extend(scope_profiles[scope] for scope in scopes)
    return scopes, _ordered_union(groups)


def semantic_projection(
    repo: Path, adapter: dict[str, object], raw_scopes: Iterable[object]
) -> dict[str, object]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    validate_scope_dependencies(adapter, scopes)
    identity_fields = (
        "platform_input", "platform_name", "platform_root", "package_root",
        "active_changes_namespace", "archive_namespace", "production_roots",
        "protected_roots", "production_exclusions", "contract_prefix",
        "boundary_guard", "extended_design_sections", "context_file_suffixes",
        "context_excluded_directories", "context_always_include_globs",
    )
    return {
        "contract": {
            **{field: adapter[field] for field in identity_fields},
            "lifecycle_capabilities": validate_capabilities(adapter),
            "platform_ux": adapter.get("platform_ux"),
        },
        "phase_rule_profiles": {phase: phases[phase] for phase in PHASES if phase in phases},
        "scope_rule_profiles": {scope: scope_profiles[scope] for scope in scopes},
        "scope_task_checks": {
            scope: adapter.get("scope_task_checks", {}).get(scope, []) for scope in scopes
        },
        "scope_dependencies": {
            scope: adapter.get("scope_dependencies", {}).get(scope, []) for scope in scopes
            if scope in adapter.get("scope_dependencies", {})
        },
    }
