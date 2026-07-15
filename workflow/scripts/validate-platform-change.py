#!/usr/bin/env python3
"""Deterministic stdlib-only validator for adapter-backed platform packages."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path

FEATURE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|TBD|FIXME)\b|<[^>\n]+>|\{\{|\}\}|\.\.\.", re.I
)
SHARED_REQ_DECL_RE = re.compile(
    r"(?m)^-\s+`(REQ-[A-Za-z0-9_-]+)`\s+[—-]\s+(.+)$"
)
SHARED_AC_DECL_RE = re.compile(
    r"(?m)^-\s+`(AC-[A-Za-z0-9_-]+)`\s+[—-]\s+(.+)$"
)
SHARED_COPY_RE = re.compile(
    r"(?m)^(?:###\s+|-\s+`?)(?:REQ|AC)-[A-Za-z0-9_-]+`?\s+[—-]"
)
REQUIRED_META = {
    "platform",
    "feature",
    "change_type",
    "tier",
    "status",
    "shared_product_spec",
    "product_status",
    "product_approval",
    "product_impact",
    "impact_evidence",
    "blocking_questions",
    "design_gate",
    "tasks_total",
}
COMMON_DESIGN_SECTIONS = (
    "Current context",
    "Proposed architecture and boundaries",
    "Data and control flow",
    "Error and recovery model",
    "Verification strategy",
)


class AdapterError(ValueError):
    """Raised when a platform adapter is absent or unsafe."""


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
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise AdapterError(f"{label} must be a safe repo-relative path")
    resolved = (repo / candidate).resolve()
    if not is_subpath(resolved, repo):
        raise AdapterError(f"{label} escapes repository root")
    return resolved


def load_adapter(repo: Path, platform: str) -> dict[str, object]:
    key = platform.lower()
    matches: list[dict[str, object]] = []
    for path in sorted(repo.glob("*/workflow/platform-contract.json")):
        try:
            data = json.loads(read(path))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("platform_input", "")).lower() == key:
            data["_path"] = str(path.relative_to(repo))
            matches.append(data)
    if not matches:
        raise AdapterError(
            f"NOT IMPLEMENTED: platform '{platform}' has no implementation adapter; "
            "no files were written"
        )
    if len(matches) != 1:
        raise AdapterError(f"platform '{platform}' has multiple adapters")
    adapter = matches[0]
    required = {
        "platform_input",
        "platform_name",
        "platform_root",
        "package_root",
        "contract_prefix",
        "boundary_guard",
        "extended_design_sections",
        "ui_task_checks",
    }
    missing = sorted(required - set(adapter))
    if missing:
        raise AdapterError(f"platform adapter missing fields: {', '.join(missing)}")
    safe_repo_path(repo, str(adapter["platform_root"]), "platform_root")
    safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    prefix = str(adapter["contract_prefix"])
    if not re.fullmatch(r"[A-Z][A-Z0-9]*", prefix):
        raise AdapterError("contract_prefix must be uppercase alphanumeric")
    return adapter


def section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", text
    )
    return match.group(1).strip() if match else None


def substantive(value: str | None, minimum: int = 12) -> bool:
    if value is None or PLACEHOLDER_RE.search(value):
        return False
    cleaned = re.sub(r"[`*_#|>\-]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned.lower() in {"n/a", "none", "нет", "not applicable", "pending"}:
        return False
    return len(cleaned) >= minimum and len(cleaned.split()) >= 2


def explicit_none(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = re.sub(r"[`*_#|>\-]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().casefold()
    cleaned = cleaned.rstrip(".!;: ")
    return cleaned in {"none", "no open questions", "нет открытых вопросов"}


def field_value(text: str, label: str) -> str | None:
    match = re.search(
        rf"(?mi)^-\s*\**{re.escape(label)}\s*:\**\s*`?([^`\n]+)`?\s*$", text
    )
    return match.group(1).strip() if match else None


def valid_human_value(value: str | None, minimum: int = 3) -> bool:
    if value is None or PLACEHOLDER_RE.search(value):
        return False
    cleaned = value.strip().strip("`* ")
    return len(cleaned) >= minimum and cleaned.lower() not in {
        "none",
        "n/a",
        "pending",
        "unknown",
        "approved",
    }


def heading_blocks(text: str, pattern: re.Pattern[str]) -> list[tuple[str, str]]:
    matches = list(pattern.finditer(text))
    result: list[tuple[str, str]] = []
    for match in matches:
        tail = text[match.end() :]
        boundary = re.search(r"(?m)^#{2,3}\s+", tail)
        body = tail[: boundary.start()] if boundary else tail
        result.append((match.group(1), body.strip()))
    return result


def parse_verification_rows(text: str) -> tuple[dict[str, list[tuple[str, str]]], list[str]]:
    rows: dict[str, list[tuple[str, str]]] = defaultdict(list)
    errors: list[str] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].lower() in {"contract id", "---"}:
            continue
        if set(cells[0]) <= {"-", ":"}:
            continue
        contract_id, _layer, method, evidence, _status = cells[:5]
        rows[contract_id].append((method, evidence))
    for contract_id, values in rows.items():
        if len(values) > 1:
            errors.append(f"verification.md duplicates row for {contract_id}")
        for method, evidence in values:
            if not substantive(method, 4):
                errors.append(f"verification.md has empty method for {contract_id}")
            if not substantive(evidence, 6):
                errors.append(f"verification.md has empty evidence for {contract_id}")
    return rows, errors


def validate_task_paths(repo: Path, raw: str, task_name: str) -> list[str]:
    errors: list[str] = []
    if PLACEHOLDER_RE.search(raw):
        return [f"{task_name} Paths contains unresolved placeholder"]
    tokens = [
        token.strip()
        for token in re.split(
            r"\s*(?:;|\|)\s*|,\s*(?=(?:existing|proposed)\s*:)", raw
        )
        if token.strip()
    ]
    if not tokens:
        return [f"{task_name} must declare non-empty Paths"]
    for token in tokens:
        match = re.fullmatch(r"(existing|proposed):\s*(.+)", token, re.I)
        if not match or not match.group(2).strip():
            errors.append(
                f"{task_name} Paths token must be existing: or proposed: with a path"
            )
            continue
        kind = match.group(1).lower()
        raw_path = match.group(2).strip()
        path_value = Path(raw_path)
        if path_value.is_absolute() or ".." in path_value.parts:
            errors.append(f"{task_name} Paths rejects absolute/traversal path: {raw_path}")
            continue
        resolved = (repo / path_value).resolve()
        if not is_subpath(resolved, repo):
            errors.append(f"{task_name} Paths escapes repository root: {raw_path}")
            continue
        if kind == "existing" and not resolved.exists():
            errors.append(f"{task_name} existing path does not exist: {raw_path}")
    return errors


def validate_design(
    text: str, tier: str, adapter: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    if PLACEHOLDER_RE.search(text):
        errors.append("design.md contains unresolved placeholder")
    if tier == "quick":
        na = re.search(r"(?mi)^Design status:\s*NOT_APPLICABLE:\s*(.+)$", text)
        if na:
            if not substantive(na.group(1), 16):
                errors.append("quick design NOT_APPLICABLE requires a substantive reason")
            return errors
    for name in COMMON_DESIGN_SECTIONS:
        if not substantive(section(text, name), 28):
            errors.append(f"design.md missing substantive section: {name}")
    if tier == "extended":
        for name in adapter["extended_design_sections"]:
            if not substantive(section(text, str(name)), 28):
                errors.append(f"extended design missing substantive section: {name}")
    return errors


def validate_package(
    repo: Path, adapter: dict[str, object], feature: str, mode: str
) -> list[str]:
    if not FEATURE_RE.fullmatch(feature):
        return ["feature must be a strict kebab-case slug"]
    errors: list[str] = []
    prefix = str(adapter["contract_prefix"])
    platform_name = str(adapter["platform_name"])
    package_root = safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    package = (package_root / feature).resolve()
    if package.parent != package_root or not is_subpath(package, package_root):
        return ["feature escapes platform package root"]
    meta_path = package / "meta.json"
    if not meta_path.is_file():
        return [f"missing {meta_path.relative_to(repo)}"]
    try:
        meta = json.loads(read(meta_path))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid meta.json: {error}"]
    missing = sorted(REQUIRED_META - set(meta))
    if missing:
        errors.append(f"meta.json missing fields: {', '.join(missing)}")
    if meta.get("platform") != platform_name:
        errors.append(f"meta.platform must be {platform_name}")
    if meta.get("feature") != feature:
        errors.append("meta.feature does not match CLI feature")
    if meta.get("change_type") not in {"product-backed", "technical-only"}:
        errors.append("change_type must be product-backed or technical-only")
    tier = str(meta.get("tier", ""))
    if tier not in {"quick", "standard", "extended"}:
        errors.append("tier must be quick, standard or extended")
    blockers = meta.get("blocking_questions")
    if not isinstance(blockers, list) or blockers:
        errors.append("blocking_questions must be an empty array before transition")

    shared_reqs: set[str] = set()
    shared_acs: set[str] = set()
    if meta.get("change_type") == "product-backed":
        expected_shared = f"specs/product/{feature}/spec.md"
        shared = meta.get("shared_product_spec")
        if shared != expected_shared:
            errors.append(
                f"shared_product_spec must be exactly {expected_shared}"
            )
        else:
            try:
                shared_path = safe_repo_path(repo, shared, "shared_product_spec")
            except AdapterError as error:
                errors.append(str(error))
            else:
                expected_root = (repo / "specs" / "product" / feature).resolve()
                if shared_path.parent != expected_root or not is_subpath(shared_path, expected_root):
                    errors.append("shared_product_spec escapes matching feature root")
                elif not shared_path.is_file():
                    errors.append(f"shared product spec missing: {shared}")
                else:
                    product = read(shared_path)
                    if PLACEHOLDER_RE.search(product):
                        errors.append("shared product spec contains unresolved placeholder")
                    if field_value(product, "Status") != "READY":
                        errors.append("shared product spec is not READY")
                    if field_value(product, "Product approval") != "APPROVED":
                        errors.append("shared product spec is not APPROVED")
                    if not valid_human_value(field_value(product, "Approved by")):
                        errors.append("shared product spec has no human approver")
                    if not valid_human_value(
                        field_value(product, "Approval evidence"), 8
                    ):
                        errors.append("shared product spec has no approval evidence")
                    shared_req_rows = SHARED_REQ_DECL_RE.findall(product)
                    shared_ac_rows = SHARED_AC_DECL_RE.findall(product)
                    shared_reqs = {item[0] for item in shared_req_rows}
                    shared_acs = {item[0] for item in shared_ac_rows}
                    if len(shared_reqs) != len(shared_req_rows):
                        errors.append("shared product spec has duplicate REQ IDs")
                    if len(shared_acs) != len(shared_ac_rows):
                        errors.append("shared product spec has duplicate AC IDs")
        if meta.get("product_status") != "READY" or meta.get("product_approval") != "APPROVED":
            errors.append("meta product status/approval must be READY/APPROVED")
        if meta.get("product_impact") != "PRESENT":
            errors.append("product-backed product_impact must be PRESENT")
    elif meta.get("change_type") == "technical-only":
        if meta.get("shared_product_spec") is not None:
            errors.append("technical-only shared_product_spec must be null")
        if meta.get("product_impact") != "NONE" or not substantive(
            str(meta.get("impact_evidence", "")), 12
        ):
            errors.append("technical-only requires Product impact NONE with evidence")

    required_files = (
        "proposal.md",
        "implementation-spec.md",
        "design.md",
        "verification.md",
    )
    for name in required_files:
        if not (package / name).is_file():
            errors.append(f"missing {name}")
    if any(not (package / name).is_file() for name in required_files):
        return errors

    proposal = read(package / "proposal.md")
    if PLACEHOLDER_RE.search(proposal):
        errors.append("proposal.md contains unresolved placeholder")
    for name in ("Intake", "Goal", "Scope", "Non-goals", "Accepted decisions", "Risks"):
        if not substantive(section(proposal, name), 16):
            errors.append(f"proposal.md missing substantive section: {name}")
    open_questions = section(proposal, "Open questions")
    if not explicit_none(open_questions):
        errors.append("proposal.md has unresolved open/blocking questions")

    spec = read(package / "implementation-spec.md")
    if PLACEHOLDER_RE.search(spec):
        errors.append("implementation-spec.md contains unresolved placeholder")
    for name in (
        "Intake reference",
        "Shared contract references",
        "Platform requirements",
        "Platform acceptance criteria",
        "Constraints",
        "Integration points",
        "Open questions",
    ):
        value = section(spec, name)
        if name == "Open questions":
            if not explicit_none(value):
                errors.append("implementation-spec.md has unresolved open questions")
        elif not substantive(value, 12):
            errors.append(f"implementation-spec.md missing substantive section: {name}")
    if SHARED_COPY_RE.search(spec):
        errors.append("shared REQ/AC declaration duplicated in implementation-spec.md")

    req_heading = re.compile(rf"(?m)^###\s+({prefix}-REQ-\d+)\s+[—-]\s+.+$")
    ac_heading = re.compile(rf"(?m)^###\s+({prefix}-AC-\d+)\s+[—-]\s+.+$")
    req_blocks = heading_blocks(spec, req_heading)
    ac_blocks = heading_blocks(spec, ac_heading)
    req_ids = [item[0] for item in req_blocks]
    ac_ids = [item[0] for item in ac_blocks]
    declared_reqs = set(req_ids)
    declared_acs = set(ac_ids)
    if not req_ids:
        errors.append(f"no {prefix}-REQ-N declarations")
    if not ac_ids:
        errors.append(f"no {prefix}-AC-N declarations")
    if len(declared_reqs) != len(req_ids):
        errors.append(f"duplicate {prefix}-REQ ID")
    if len(declared_acs) != len(ac_ids):
        errors.append(f"duplicate {prefix}-AC ID")
    for req_id, body in req_blocks:
        if not substantive(body, 16):
            errors.append(f"{req_id} has no substantive contract")
    covered: set[str] = set()
    req_ref_re = re.compile(rf"\b{prefix}-REQ-\d+\b")
    for ac_id, body in ac_blocks:
        covers = re.search(r"(?mi)^`?Covers\s*:\s*([^`\n]+)`?\s*$", body)
        refs = set(req_ref_re.findall(covers.group(1))) if covers else set()
        outcome = body[: covers.start()].strip() if covers else body
        if not substantive(outcome, 16):
            errors.append(f"{ac_id} has no substantive observable outcome")
        if not refs:
            errors.append(f"{ac_id} has no Covers: {prefix}-REQ-N")
        unknown = refs - declared_reqs
        for req_id in sorted(unknown):
            errors.append(f"{ac_id} covers undeclared {req_id}")
        covered |= refs & declared_reqs
    for req_id in sorted(declared_reqs - covered):
        errors.append(f"{req_id} is not covered by a declared platform AC")

    design = read(package / "design.md")
    design_errors = validate_design(design, tier, adapter)
    errors.extend(design_errors)
    if str(meta.get("design_gate")) != "PASS":
        errors.append("meta.design_gate must be PASS after content-based design validation")

    verification = read(package / "verification.md")
    if PLACEHOLDER_RE.search(verification):
        errors.append("verification.md contains unresolved placeholder")
    rows, row_errors = parse_verification_rows(verification)
    errors.extend(row_errors)
    for contract_id in sorted(
        shared_reqs | shared_acs | declared_reqs | declared_acs
    ):
        if contract_id not in rows:
            errors.append(f"verification.md does not trace {contract_id}")

    if mode == "propose":
        if meta.get("status") != "specified":
            errors.append("propose mode requires status specified")
        if meta.get("tasks_total") != 0:
            errors.append("specified package tasks_total must be 0")
        return errors

    if meta.get("status") != "planned":
        errors.append("plan mode requires status planned")
    plan_root = package / "plan"
    tasks = sorted(plan_root.glob("task-*.md")) if plan_root.is_dir() else []
    expected_names = [f"task-{index:03d}.md" for index in range(1, len(tasks) + 1)]
    if [path.name for path in tasks] != expected_names:
        errors.append("plan task numbering must be continuous from task-001")
    plan_readme = plan_root / "README.md"
    if not plan_readme.is_file():
        errors.append("plan/README.md is missing")
        plan_index = ""
    else:
        plan_index = read(plan_readme)
        if PLACEHOLDER_RE.search(plan_index):
            errors.append("plan/README.md contains unresolved placeholder")
        for name in (
            "Planning frame",
            "DAG",
            "Estimates and multipliers",
            "Verification strategy",
        ):
            if not substantive(section(plan_index, name), 16):
                errors.append(f"plan/README.md missing substantive section: {name}")
    if meta.get("tasks_total") != len(tasks) or not tasks:
        errors.append("tasks_total must equal a non-zero task count")

    task_ids = {path.stem for path in tasks}
    dependencies: dict[str, set[str]] = {}
    known_context_ids = shared_reqs | shared_acs | declared_reqs | declared_acs
    known_req_ids = shared_reqs | declared_reqs
    known_ac_ids = shared_acs | declared_acs
    for task in tasks:
        body = read(task)
        if PLACEHOLDER_RE.search(body):
            errors.append(f"{task.name} contains unresolved placeholder")
        for name in (
            "Goal",
            "Inline contract context",
            "Steps",
            "Verification",
            "Expected result",
            "Out of scope",
        ):
            if not substantive(section(body, name), 12):
                errors.append(f"{task.name} missing substantive section: {name}")
        context = section(body, "Inline contract context") or ""
        context_ids = set(re.findall(r"\b(?:REQ|AC|[A-Z][A-Z0-9]*-(?:REQ|AC))-\d+\b", context))
        if not (context_ids & known_req_ids) or not (context_ids & known_ac_ids):
            errors.append(
                f"{task.name} inline context must include declared requirement and AC IDs"
            )
        unknown_context = context_ids - known_context_ids
        if unknown_context:
            errors.append(
                f"{task.name} inline context references unknown IDs: {', '.join(sorted(unknown_context))}"
            )

        layer_match = re.findall(r"(?mi)^-\s*Layer:\s*([^\n]+)", body)
        allowed_layers = {"domain", "data", "presentation", "infrastructure", "tests"}
        layer = layer_match[0].strip().lower() if len(layer_match) == 1 else ""
        if layer not in allowed_layers:
            errors.append(f"{task.name} must declare exactly one allowed Layer")
        if layer == "presentation":
            for check in adapter["ui_task_checks"]:
                if str(check).lower() not in body.lower():
                    errors.append(f"{task.name} presentation task missing {check} check")

        paths = re.search(r"(?mi)^-\s*Paths:\s*(.+)$", body)
        if not paths:
            errors.append(f"{task.name} must declare non-empty Paths")
        else:
            errors.extend(validate_task_paths(repo, paths.group(1), task.name))

        estimate = re.search(
            r"(?mi)^-\s*Estimate \(ideal\):\s*([0-9.]+)\s*[–-]\s*([0-9.]+)\s*days\s*$",
            body,
        )
        if not estimate:
            errors.append(f"{task.name} has invalid ideal estimate format")
        else:
            minimum, maximum = map(float, estimate.groups())
            if not (0 < minimum <= maximum <= 2):
                errors.append(
                    f"{task.name} estimate must satisfy 0 < min <= max <= 2"
                )

        dependency_line = re.search(r"(?mi)^-\s*Depends on:\s*(.+)$", body)
        deps: set[str] = set()
        if not dependency_line:
            errors.append(f"{task.name} missing Depends on")
        else:
            raw = dependency_line.group(1).strip()
            if raw.lower() not in {"none", "—", "-"}:
                deps = set(re.findall(r"\btask-\d{3}\b", raw))
                if not deps:
                    errors.append(f"{task.name} has invalid dependency declaration")
                for dep in sorted(deps - task_ids):
                    errors.append(f"{task.name} depends on missing {dep}")
                if task.stem in deps:
                    errors.append(f"{task.name} depends on itself")
        dependencies[task.stem] = deps

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dependency in dependencies.get(node, set()):
            if dependency in task_ids and visit(dependency):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(visit(node) for node in sorted(task_ids)):
        errors.append("plan dependency graph contains a cycle")
    dag_section = section(plan_index, "DAG") or ""
    for task_id in sorted(task_ids):
        if task_id not in dag_section:
            errors.append(f"plan README DAG does not mention {task_id}")
    return errors


def write_baseline(repo: Path) -> tuple[Path, Path, dict[str, object]]:
    adapter_dir = repo / "TestClient" / "workflow"
    adapter_dir.mkdir(parents=True)
    adapter = {
        "platform_input": "test-client",
        "platform_name": "TestClient",
        "platform_root": "TestClient",
        "package_root": "TestClient/specs",
        "contract_prefix": "TST",
        "boundary_guard": "test-client-boundary-guard",
        "extended_design_sections": [
            "System-design review",
            "Platform SDK considerations",
            "Execution model",
            "Platform verification gates",
        ],
        "ui_task_checks": ["simulator", "accessibility", "design-system"],
    }
    (adapter_dir / "platform-contract.json").write_text(
        json.dumps(adapter), encoding="utf-8"
    )
    product = repo / "specs" / "product" / "sample" / "spec.md"
    product.parent.mkdir(parents=True)
    product.write_text(
        "- **Status:** `READY`\n"
        "- **Product approval:** `APPROVED`\n"
        "- **Approved by:** Mobile product owner\n"
        "- **Approval evidence:** Decision recorded in review meeting 2026-07-15\n\n"
        "## Requirements\n- `REQ-1` — Shared observable requirement\n\n"
        "## Acceptance Criteria\n- `AC-1` — Shared observable outcome. `Covers: REQ-1`\n",
        encoding="utf-8",
    )
    package = repo / "TestClient" / "specs" / "sample"
    package.mkdir(parents=True)
    meta: dict[str, object] = {
        "platform": "TestClient",
        "feature": "sample",
        "change_type": "product-backed",
        "tier": "standard",
        "status": "specified",
        "shared_product_spec": "specs/product/sample/spec.md",
        "product_status": "READY",
        "product_approval": "APPROVED",
        "product_impact": "PRESENT",
        "impact_evidence": "Approved shared product contract applies to this package",
        "blocking_questions": [],
        "design_gate": "PASS",
        "tasks_total": 0,
    }
    (package / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (package / "proposal.md").write_text(
        "# Proposal\n\n"
        "## Intake\nProduct-backed intake references the approved shared contract.\n\n"
        "## Goal\nCreate an implementation boundary for the selected client.\n\n"
        "## Scope\nPlatform architecture and verification mapping are included.\n\n"
        "## Non-goals\nProduction implementation and other clients remain outside scope.\n\n"
        "## Accepted decisions\nUse the platform adapter and preserve shared behavior IDs.\n\n"
        "## Open questions\nNone.\n\n"
        "## Risks\nGreenfield paths remain proposed until source files exist.\n",
        encoding="utf-8",
    )
    (package / "implementation-spec.md").write_text(
        "# Implementation spec\n\n"
        "## Intake reference\nProduct-backed package for the approved shared contract.\n\n"
        "## Shared contract references\nReferences REQ-1 and AC-1 without copying behavior.\n\n"
        "## Platform requirements\n"
        "### TST-REQ-1 — Platform boundary\n"
        "The client isolates integration behind a testable platform contract.\n\n"
        "## Platform acceptance criteria\n"
        "### TST-AC-1 — Boundary verification\n"
        "The integration test observes the platform boundary returning its result.\n"
        "Covers: TST-REQ-1\n\n"
        "## Constraints\nThe shared observable behavior remains unchanged.\n\n"
        "## Integration points\nThe proposed module connects through the application composition root.\n\n"
        "## Open questions\nNo open questions.\n",
        encoding="utf-8",
    )
    (package / "design.md").write_text(
        "# Design\n\n"
        "## Current context\nThe client source is greenfield, so all implementation paths are proposed.\n\n"
        "## Proposed architecture and boundaries\nA feature boundary separates domain contracts from platform integrations.\n\n"
        "## Data and control flow\nActions enter the domain boundary and results return through typed outputs.\n\n"
        "## Error and recovery model\nPlatform failures map to explicit errors and support deterministic retry.\n\n"
        "## Verification strategy\nUnit and integration tests verify boundaries before simulator evidence.\n",
        encoding="utf-8",
    )
    (package / "verification.md").write_text(
        "# Verification\n\n"
        "| Contract ID | Layer | Method | Expected evidence | Status |\n"
        "|---|---|---|---|---|\n"
        "| REQ-1 | contract | Shared requirement review | Approved contract record | pending |\n"
        "| AC-1 | integration | Shared behavior scenario | Recorded scenario result | pending |\n"
        "| TST-REQ-1 | design | Platform requirement review | Design review record | pending |\n"
        "| TST-AC-1 | unit | Boundary contract test | Passing test report | pending |\n",
        encoding="utf-8",
    )
    return product, package, meta


def assert_red(errors: list[str], name: str) -> None:
    assert errors, f"RED fixture unexpectedly passed: {name}"


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve()
        product, package, meta = write_baseline(repo)
        adapter = load_adapter(repo, "test-client")
        assert validate_package(repo, adapter, "sample", "propose") == []

        # Intake and path safety RED fixtures.
        for unsafe in ("../../escape", "/tmp/escape", "specs/product/other/spec.md"):
            changed = dict(meta); changed["shared_product_spec"] = unsafe
            (package / "meta.json").write_text(json.dumps(changed), encoding="utf-8")
            assert_red(validate_package(repo, adapter, "sample", "propose"), f"unsafe shared path {unsafe}")
        (package / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "../../escape", "propose"), "traversal feature")
        assert_red(validate_package(repo, adapter, "/absolute", "propose"), "absolute feature")

        original_product = read(product)
        product.write_text(
            "- **Status:** `READY`\n- **Product approval:** `APPROVED`\n"
            "- **Approved by:** <person>\n- **Approval evidence:** <evidence>\n",
            encoding="utf-8",
        )
        assert_red(validate_package(repo, adapter, "sample", "propose"), "placeholder approval")
        product.write_text(original_product, encoding="utf-8")

        original_proposal = read(package / "proposal.md")
        (package / "proposal.md").write_text(
            original_proposal.replace(
                "None.",
                "Нет решения; BLOCKING: storage contract remains unknown",
            ),
            encoding="utf-8",
        )
        assert_red(validate_package(repo, adapter, "sample", "propose"), "proposal blocker")
        (package / "proposal.md").write_text(original_proposal, encoding="utf-8")

        original_spec = read(package / "implementation-spec.md")
        bad_spec = original_spec.replace("Covers: TST-REQ-1", "Covers: TST-REQ-999")
        (package / "implementation-spec.md").write_text(bad_spec, encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "propose"), "undeclared Covers")
        duplicate_spec = original_spec.replace(
            "## Platform acceptance criteria",
            "### TST-REQ-1 — Duplicate\nDuplicate requirement body is invalid.\n\n## Platform acceptance criteria",
        )
        (package / "implementation-spec.md").write_text(duplicate_spec, encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "propose"), "duplicate requirement")
        duplicate_ac = original_spec + (
            "\n### TST-AC-1 — Duplicate outcome\n"
            "A duplicate identifier must be rejected.\nCovers: TST-REQ-1\n"
        )
        (package / "implementation-spec.md").write_text(duplicate_ac, encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "propose"), "duplicate acceptance criterion")
        (package / "implementation-spec.md").write_text(original_spec, encoding="utf-8")

        original_design = read(package / "design.md")
        extended = dict(meta); extended["tier"] = "extended"
        (package / "meta.json").write_text(json.dumps(extended), encoding="utf-8")
        headings_only = original_design + "\n".join(
            f"## {name}\n" for name in adapter["extended_design_sections"]
        )
        (package / "design.md").write_text(headings_only, encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "propose"), "headings-only extended design")
        (package / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        (package / "design.md").write_text(original_design, encoding="utf-8")

        original_verification = read(package / "verification.md")
        (package / "verification.md").write_text(
            original_verification.replace("Boundary contract test", "—"),
            encoding="utf-8",
        )
        assert_red(validate_package(repo, adapter, "sample", "propose"), "empty verification method")
        (package / "verification.md").write_text(
            original_verification.replace("Passing test report", "—"),
            encoding="utf-8",
        )
        assert_red(validate_package(repo, adapter, "sample", "propose"), "empty verification evidence")
        (package / "verification.md").write_text(original_verification, encoding="utf-8")

        # Positive plan followed by adversarial task/DAG fixtures.
        planned = dict(meta); planned["status"] = "planned"; planned["tasks_total"] = 2
        (package / "meta.json").write_text(json.dumps(planned), encoding="utf-8")
        plan = package / "plan"; plan.mkdir()
        (plan / "README.md").write_text(
            "# Plan\n\n## Planning frame\nImplement two bounded layers after approved specification.\n\n"
            "## DAG\ntask-001 precedes task-002 through an explicit dependency.\n\n"
            "## Estimates and multipliers\nThe range includes a documented greenfield uncertainty multiplier.\n\n"
            "## Verification strategy\nEach task has an isolated test and expected result.\n",
            encoding="utf-8",
        )
        task_1 = (
            "# task-001\n- Layer: domain\n- Depends on: none\n"
            "- Paths: proposed: Sources/Sample/Domain; existing: specs/product/sample/spec.md\n"
            "- Estimate (ideal): 0.5–1 days\n\n"
            "## Goal\nCreate the typed platform boundary contract.\n\n"
            "## Inline contract context\nTST-REQ-1 requires a testable boundary; TST-AC-1 observes its result.\n\n"
            "## Steps\nDefine the boundary and its typed input and output contracts.\n\n"
            "## Verification\nRun the isolated domain contract test.\n\n"
            "## Expected result\nThe contract test passes with typed output.\n"
            "\n## Out of scope\nPlatform integration and presentation wiring remain separate tasks.\n"
        )
        task_2 = (
            "# task-002\n- Layer: tests\n- Depends on: task-001\n"
            "- Paths: proposed: Tests/Sample/BoundaryTests\n- Estimate (ideal): 0.5–1 days\n\n"
            "## Goal\nAdd regression coverage for the boundary.\n\n"
            "## Inline contract context\nTST-REQ-1 defines the boundary; TST-AC-1 requires observable verification.\n\n"
            "## Steps\nCreate the focused regression test and deterministic fixture.\n\n"
            "## Verification\nRun the focused regression suite.\n\n"
            "## Expected result\nThe regression suite records passing evidence.\n"
            "\n## Out of scope\nProduction source changes remain outside this tests-only task.\n"
        )
        (plan / "task-001.md").write_text(task_1, encoding="utf-8")
        (plan / "task-002.md").write_text(task_2, encoding="utf-8")
        assert validate_package(repo, adapter, "sample", "plan") == []

        (plan / "task-001.md").write_text(task_1.replace("TST-REQ-1 requires a testable boundary; TST-AC-1 observes its result.", ""), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "empty inline context")
        (plan / "task-001.md").write_text(task_1, encoding="utf-8")

        (plan / "task-001.md").write_text(task_1.replace("## Steps\nDefine the boundary and its typed input and output contracts.\n\n", ""), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "missing Steps")
        (plan / "task-001.md").write_text(task_1.replace("\n## Out of scope\nPlatform integration and presentation wiring remain separate tasks.\n", ""), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "missing Out of scope")
        (plan / "task-001.md").write_text(task_1, encoding="utf-8")

        (plan / "task-001.md").write_text(task_1.replace("proposed: Sources/Sample/Domain", "proposed:"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "empty paths")
        (plan / "task-001.md").write_text(task_1.replace("proposed: Sources/Sample/Domain", "existing: Missing/Source.swift"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "nonexistent existing path")
        (plan / "task-001.md").write_text(task_1.replace("proposed: Sources/Sample/Domain", "proposed: ../../escape"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "traversal task path")
        (plan / "task-001.md").write_text(task_1.replace("proposed: Sources/Sample/Domain", "proposed: /tmp/escape"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "absolute task path")
        (plan / "task-001.md").write_text(task_1, encoding="utf-8")

        (plan / "task-001.md").write_text(task_1.replace("0.5–1 days", "1.5–0.5 days"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "reversed estimate")
        (plan / "task-001.md").write_text(task_1, encoding="utf-8")

        (plan / "task-001.md").write_text(task_1.replace("Depends on: none", "Depends on: task-002"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "cyclic DAG")
        (plan / "task-001.md").write_text(task_1.replace("Depends on: none", "Depends on: task-999"), encoding="utf-8")
        assert_red(validate_package(repo, adapter, "sample", "plan"), "missing dependency")

    print("validate-platform-change self-test: PASS (all adversarial fixtures RED)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform")
    parser.add_argument("--feature")
    parser.add_argument("--mode", choices=("propose", "plan"))
    parser.add_argument("--root", type=Path, default=repository_root())
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.platform or not args.feature or not args.mode:
        parser.error("--platform, --feature and --mode are required")
    if not FEATURE_RE.fullmatch(args.feature):
        print("BLOCKED: feature must be a strict kebab-case slug; no files were written.")
        return 3
    repo = args.root.resolve()
    try:
        adapter = load_adapter(repo, args.platform)
        errors = validate_package(repo, adapter, args.feature, args.mode)
    except AdapterError as error:
        print(f"BLOCKED: {error}.")
        return 4
    if errors:
        print(f"Platform package: INVALID ({len(errors)} blocker)")
        for error in errors:
            print(f"- {error}")
        return 2
    platform_name = adapter["platform_name"]
    print(f"Platform package: VALID ({args.mode}, {platform_name}/{args.feature})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
