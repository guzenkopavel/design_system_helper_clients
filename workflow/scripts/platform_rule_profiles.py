#!/usr/bin/env python3
"""Canonical validation and resolution for platform engineering rule profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re

PHASES = ("propose", "plan", "implement", "verify")
SCOPE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class RuleProfileError(ValueError):
    pass


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
    phase_value = adapter.get("phase_rule_profiles")
    if not isinstance(phase_value, dict) or set(phase_value) != set(PHASES):
        raise RuleProfileError("phase_rule_profiles must contain exact propose/plan/implement/verify keys")
    phases = {
        phase: _rule_list(repo, phase_value[phase], f"phase_rule_profiles.{phase}", require_files)
        for phase in PHASES
    }
    scope_value = adapter.get("scope_rule_profiles")
    if not isinstance(scope_value, dict) or not scope_value:
        raise RuleProfileError("scope_rule_profiles must be a non-empty object")
    scopes: dict[str, list[str]] = {}
    for scope, rules in scope_value.items():
        if not isinstance(scope, str) or not SCOPE_RE.fullmatch(scope):
            raise RuleProfileError(f"invalid engineering scope: {scope}")
        scopes[scope] = _rule_list(repo, rules, f"scope_rule_profiles.{scope}", require_files)
    profiled = {rule for rules in phases.values() for rule in rules}
    profiled.update(rule for rules in scopes.values() for rule in rules)
    unknown = sorted(profiled - set(catalog))
    unused = sorted(set(catalog) - profiled)
    if unknown:
        raise RuleProfileError(f"profile rules missing from rule_files catalog: {', '.join(unknown)}")
    if unused:
        raise RuleProfileError(f"rule_files entries are not assigned to a profile: {', '.join(unused)}")
    return catalog, phases, scopes


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
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    return scopes, _ordered_union([phases[phase], *(scope_profiles[scope] for scope in scopes)])


def applicable_rules(
    repo: Path, adapter: dict[str, object], raw_scopes: Iterable[object],
    require_files: bool = True,
) -> tuple[list[str], list[str]]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter, require_files)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    groups = [phases[phase] for phase in PHASES]
    groups.extend(scope_profiles[scope] for scope in scopes)
    return scopes, _ordered_union(groups)


def semantic_projection(
    repo: Path, adapter: dict[str, object], raw_scopes: Iterable[object]
) -> dict[str, object]:
    _catalog, phases, scope_profiles = validate_profiles(repo, adapter)
    scopes = normalize_scopes(raw_scopes, scope_profiles)
    identity_fields = (
        "platform_input", "platform_name", "platform_root", "package_root",
        "active_changes_namespace", "archive_namespace", "production_roots",
        "protected_roots", "production_exclusions", "contract_prefix",
        "boundary_guard", "extended_design_sections", "context_file_suffixes",
        "context_excluded_directories", "context_always_include_globs",
    )
    return {
        "contract": {field: adapter[field] for field in identity_fields},
        "phase_rule_profiles": {phase: phases[phase] for phase in PHASES},
        "scope_rule_profiles": {scope: scope_profiles[scope] for scope in scopes},
        "scope_task_checks": {
            scope: adapter.get("scope_task_checks", {}).get(scope, []) for scope in scopes
        },
    }
