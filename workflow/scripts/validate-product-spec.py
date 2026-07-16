#!/usr/bin/env python3
"""Fingerprint and validate shared product review provenance attestations."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

import artifact_language


LENSES = (
    "product",
    "ux-accessibility",
    "design-system",
    "data-analytics-privacy",
    "security",
    "cross-client-parity",
)
ALWAYS_REQUIRED = {"product", "cross-client-parity"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
PROVENANCE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\s<>]{8,512}$")
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>|\b(?:TODO|TBD|FIXME|UNKNOWN)\b", re.IGNORECASE)
STATUS_LINE_RE = re.compile(rb"(?m)^- \*\*Status:\*\* `(DRAFT|READY)`\r?$")
REQ_RE = re.compile(r"(?m)^-\s+`(REQ-[A-Za-z0-9_-]+)`\s+[—-]\s+(.+)$")
AC_RE = re.compile(r"(?m)^-\s+`(AC-[A-Za-z0-9_-]+)`\s+[—-]\s+(.+)$")
DIMENSION_RE = re.compile(r"`Verification dimension:\s*([a-z0-9]+(?:-[a-z0-9]+)*)`")
VERDICT_KEYS = {
    "schema_version", "feature", "lens", "subject_fingerprint",
    "reviewer_role", "runtime", "run_id", "parent_context_id", "context_id",
    "provenance_ref", "independent_context",
    "applicability", "verdict", "clients_checked", "rationale",
    "evidence_refs", "findings",
}
RUNTIMES = {"codex", "claude-code", "cursor", "opencode", "external"}
FINDING_KEYS = {"id", "severity", "summary", "evidence", "requirement_ids"}
RECEIPT_KEYS = {
    "schema_version", "feature", "subject_fingerprint", "coordinator_role",
    "lens_order", "aggregate_status", "verdicts",
}


class ProductSpecError(ValueError):
    pass


def repository_root(start: Path | None = None) -> Path:
    return (start or Path(__file__).resolve().parents[2]).resolve()


def substantive(value: object, minimum: int = 8) -> bool:
    text = str(value or "").strip()
    return len(text) >= minimum and not PLACEHOLDER_RE.search(text)


def safe_feature(feature: str) -> str:
    if not SLUG_RE.fullmatch(feature):
        raise ProductSpecError("feature must be strict kebab-case")
    return feature


def package_path(repo: Path, feature: str) -> Path:
    package = repo / "specs" / "product" / safe_feature(feature)
    if package.is_symlink():
        raise ProductSpecError(f"active product package root symlink is forbidden: specs/product/{feature}")
    if not package.is_dir():
        raise ProductSpecError(f"active product package is missing: specs/product/{feature}")
    return package


def normalized_payload(relative: str, payload: bytes) -> bytes:
    if relative == "spec.md":
        if len(STATUS_LINE_RE.findall(payload)) != 1:
            raise ProductSpecError("spec.md must contain exactly one exact Status metadata line")
        return STATUS_LINE_RE.sub(b"- **Status:** `<NORMALIZED>`", payload)
    return payload


def snapshot_product(repo: Path, feature: str) -> dict[str, object]:
    package = package_path(repo, feature)
    files: dict[str, str] = {}
    for base, directories, filenames in os.walk(package, followlinks=False):
        directories.sort(); filenames.sort()
        for name in list(directories):
            path = Path(base) / name
            if path.is_symlink():
                raise ProductSpecError(f"product package symlink is forbidden: {path.relative_to(repo)}")
        for name in filenames:
            path = Path(base) / name
            relative = path.relative_to(package).as_posix()
            if relative == "review-verdicts.json":
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ProductSpecError(f"product package symlink is forbidden: {path.relative_to(repo)}")
            if not stat.S_ISREG(info.st_mode):
                raise ProductSpecError(f"product package path must be a regular file: {path.relative_to(repo)}")
            if relative == "SPECIFICATION.md":
                continue
            payload = normalized_payload(relative, path.read_bytes())
            files[relative] = hashlib.sha256(payload).hexdigest()
    if "spec.md" not in files:
        raise ProductSpecError("active product package requires spec.md")
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": 1,
        "feature": feature,
        "fingerprint": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        "files": files,
    }


def load_json_file(path: Path, label: str) -> dict[str, object]:
    try:
        info = path.lstat()
    except OSError as error:
        raise ProductSpecError(f"{label} cannot be read: {error}") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024:
        raise ProductSpecError(f"{label} must be a bounded regular JSON file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProductSpecError(f"{label} JSON is invalid: {error}") from error
    if not isinstance(value, dict):
        raise ProductSpecError(f"{label} must be a JSON object")
    return value


def validate_finding(value: object, lens: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{lens} finding must be an object"]
    if set(value) != FINDING_KEYS:
        errors.append(f"{lens} finding schema must be exact")
        return errors
    if not IDENTITY_RE.fullmatch(str(value.get("id", ""))):
        errors.append(f"{lens} finding id is invalid")
    if value.get("severity") not in {"blocker", "major", "minor", "info"}:
        errors.append(f"{lens} finding severity is invalid")
    if not substantive(value.get("summary"), 8):
        errors.append(f"{lens} finding summary is not substantive")
    if not substantive(value.get("evidence"), 8):
        errors.append(f"{lens} finding evidence is not substantive")
    errors.extend(artifact_language.validate_authored_json_string(
        value.get("summary"), f"{lens} finding.summary"
    ))
    errors.extend(artifact_language.validate_authored_json_string(
        value.get("evidence"), f"{lens} finding.evidence"
    ))
    requirement_ids = value.get("requirement_ids")
    if not isinstance(requirement_ids, list) or not all(
        isinstance(item, str) and re.fullmatch(r"(?:REQ|AC)-[A-Za-z0-9_-]+", item)
        for item in requirement_ids
    ):
        errors.append(f"{lens} finding requirement_ids must be contract IDs")
    return errors


def validate_verdict_data(
    verdict: dict[str, object], subject: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    lens = str(verdict.get("lens", "<missing>"))
    if set(verdict) != VERDICT_KEYS:
        errors.append(f"{lens} verdict schema must be exact")
        return errors
    if verdict.get("schema_version") != 1:
        errors.append(f"{lens} verdict schema_version must be 1")
    if verdict.get("feature") != subject["feature"]:
        errors.append(f"{lens} verdict feature mismatch")
    if lens not in LENSES:
        errors.append(f"unknown review lens: {lens}")
    if verdict.get("subject_fingerprint") != subject["fingerprint"]:
        errors.append(f"{lens} verdict fingerprint is stale or mixed")
    if verdict.get("reviewer_role") != "product-spec-reviewer":
        errors.append(f"{lens} verdict must come from product-spec-reviewer, not the author/writer")
    runtime = verdict.get("runtime")
    if not isinstance(runtime, str) or runtime not in RUNTIMES:
        errors.append(f"{lens} runtime is invalid")
    for field in ("run_id", "parent_context_id", "context_id"):
        if not IDENTITY_RE.fullmatch(str(verdict.get(field, ""))):
            errors.append(f"{lens} {field} is invalid")
    provenance_ref = str(verdict.get("provenance_ref", ""))
    if not PROVENANCE_RE.fullmatch(provenance_ref) or not substantive(provenance_ref, 12):
        errors.append(f"{lens} provenance_ref must identify runtime-issued invocation evidence")
    elif (
        runtime == "external"
        and not provenance_ref.startswith("external-evidence:")
        and verdict.get("verdict") != "UNKNOWN"
    ):
        errors.append(f"{lens} external review requires explicit external-evidence provenance")
    elif isinstance(runtime, str) and runtime in RUNTIMES - {"external"} and not provenance_ref.startswith(f"{runtime}:"):
        errors.append(f"{lens} provenance_ref must match runtime {runtime}")
    independent = verdict.get("independent_context")
    if not isinstance(independent, bool):
        errors.append(f"{lens} independent_context must be boolean")
    applicability = verdict.get("applicability")
    decision = verdict.get("verdict")
    if applicability not in {"REQUIRED", "NOT_APPLICABLE"}:
        errors.append(f"{lens} applicability is invalid")
    if lens in ALWAYS_REQUIRED and applicability != "REQUIRED":
        errors.append(f"{lens} is always REQUIRED and cannot be N/A")
    if applicability == "REQUIRED" and decision not in {"PASS", "GAP", "UNKNOWN"}:
        errors.append(f"{lens} REQUIRED verdict must be PASS, GAP or UNKNOWN")
    if applicability == "NOT_APPLICABLE" and decision != "N/A":
        errors.append(f"{lens} NOT_APPLICABLE verdict must be N/A")
    if decision == "N/A" and applicability != "NOT_APPLICABLE":
        errors.append(f"{lens} N/A verdict requires NOT_APPLICABLE")
    if independent is False and decision != "UNKNOWN":
        errors.append(f"{lens} same-context fallback must be UNKNOWN")
    if verdict.get("context_id") == verdict.get("parent_context_id"):
        if independent is not False:
            errors.append(f"{lens} parent and reviewer context match; independent_context must be false")
        if decision != "UNKNOWN":
            errors.append(f"{lens} parent and reviewer context match; verdict must be UNKNOWN")
    elif independent is False:
        errors.append(f"{lens} unavailable independence must use the parent context identity")
    if decision in {"PASS", "N/A"} and independent is not True:
        errors.append(f"{lens} {decision} requires independent_context true")
    if verdict.get("clients_checked") != ["iOS", "Android"]:
        errors.append(f"{lens} must check both clients exactly: iOS and Android")
    evidence_refs = verdict.get("evidence_refs")
    subject_files = set(subject.get("files", {}))
    if not isinstance(evidence_refs, list) or not all(
        isinstance(item, str) and item in subject_files for item in evidence_refs
    ):
        errors.append(f"{lens} evidence_refs must name product package subject files")
    if not substantive(verdict.get("rationale"), 16) or not evidence_refs:
        errors.append(f"{lens} every verdict requires substantive rationale and package evidence_refs")
    errors.extend(artifact_language.validate_authored_json_string(
        verdict.get("rationale"), f"{lens} verdict.rationale"
    ))
    if decision == "N/A" and (
        not substantive(verdict.get("rationale"), 16) or not evidence_refs
    ):
        errors.append(f"{lens} N/A requires substantive package-derived rationale")
    findings = verdict.get("findings")
    if not isinstance(findings, list):
        errors.append(f"{lens} findings must be an array")
        findings = []
    finding_ids: list[str] = []
    for finding in findings:
        errors.extend(validate_finding(finding, lens))
        if isinstance(finding, dict):
            finding_ids.append(str(finding.get("id", "")))
    if len(finding_ids) != len(set(finding_ids)):
        errors.append(f"{lens} finding IDs must be unique")
    if decision == "PASS" and any(
        isinstance(item, dict) and item.get("severity") == "blocker" for item in findings
    ):
        errors.append(f"{lens} PASS cannot contain blocker findings")
    if decision in {"GAP", "UNKNOWN"} and (
        not findings or not substantive(verdict.get("rationale"), 12)
    ):
        errors.append(f"{lens} {decision} requires findings and evidence rationale")
    return errors


def validate_verdict_file(repo: Path, feature: str, path: Path) -> tuple[dict[str, object], list[str]]:
    subject = snapshot_product(repo, feature)
    verdict = load_json_file(path, "review verdict")
    return verdict, validate_verdict_data(verdict, subject)


def aggregate_data(
    repo: Path, feature: str, verdicts: list[dict[str, object]]
) -> tuple[dict[str, object] | None, list[str]]:
    subject = snapshot_product(repo, feature)
    errors: list[str] = []
    if len(verdicts) != len(LENSES):
        errors.append("aggregate requires exactly six verdicts")
    for verdict in verdicts:
        errors.extend(validate_verdict_data(verdict, subject))
    lens_names = [str(item.get("lens", "")) for item in verdicts]
    if set(lens_names) != set(LENSES) or len(lens_names) != len(set(lens_names)):
        errors.append("aggregate requires the exact six unique lenses")
    run_ids = [str(item.get("run_id", "")) for item in verdicts]
    context_ids = [str(item.get("context_id", "")) for item in verdicts]
    if len(run_ids) != len(set(run_ids)):
        errors.append("aggregate requires unique run_id per lens")
    if len(context_ids) != len(set(context_ids)):
        errors.append("one review context cannot review multiple lenses")
    provenance_refs = [str(item.get("provenance_ref", "")) for item in verdicts]
    if len(provenance_refs) != len(set(provenance_refs)):
        errors.append("aggregate requires unique invocation provenance per lens")
    parent_context_ids = [str(item.get("parent_context_id", "")) for item in verdicts]
    if len(set(parent_context_ids)) != 1:
        errors.append("aggregate requires one parent coordinator review session")
    if errors:
        return None, sorted(set(errors))
    ordered = sorted(verdicts, key=lambda item: LENSES.index(str(item["lens"])))
    decisions = {str(item["verdict"]) for item in verdicts}
    aggregate_status = "UNKNOWN" if "UNKNOWN" in decisions else "GAPS" if "GAP" in decisions else "PASS"
    return {
        "schema_version": 1,
        "feature": feature,
        "subject_fingerprint": subject["fingerprint"],
        "coordinator_role": "elaborate-coordinator",
        "lens_order": list(LENSES),
        "aggregate_status": aggregate_status,
        "verdicts": ordered,
    }, []


def write_receipt(repo: Path, feature: str, receipt: dict[str, object]) -> Path:
    package = package_path(repo, feature)
    target = package / "review-verdicts.json"
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    descriptor, temporary = tempfile.mkstemp(
        prefix=".review-verdicts-", suffix=".tmp", dir=package
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, target)
    finally:
        try:
            os.unlink(temporary)
        except OSError:
            pass
    return target


def field_values(text: str, field: str) -> list[str]:
    return [
        item.strip().strip("`")
        for item in re.findall(
            rf"(?mi)^-\s+\*\*{re.escape(field)}:\*\*\s+(.+?)\s*$", text
        )
    ]


def exact_metadata(text: str, fields: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    errors: list[str] = []
    for field in fields:
        matches = field_values(text, field)
        if len(matches) != 1:
            errors.append(f"{field} metadata must appear exactly once")
            continue
        values[field] = matches[0]
    return values, errors


def requirement_coverage(spec: str) -> list[str]:
    errors: list[str] = []
    requirement_rows = REQ_RE.findall(spec)
    criterion_rows = AC_RE.findall(spec)
    requirement_ids = [item[0] for item in requirement_rows]
    criterion_ids = [item[0] for item in criterion_rows]
    duplicate_requirements = sorted(
        identity for identity, count in Counter(requirement_ids).items() if count > 1
    )
    duplicate_criteria = sorted(
        identity for identity, count in Counter(criterion_ids).items() if count > 1
    )
    if duplicate_requirements:
        errors.append(f"duplicate REQ IDs: {', '.join(duplicate_requirements)}")
    if duplicate_criteria:
        errors.append(f"duplicate AC IDs: {', '.join(duplicate_criteria)}")
    requirements = set(requirement_ids)
    if not requirement_rows or not criterion_rows:
        return ["product spec requires at least one REQ and one AC"]
    covered: set[str] = set()
    dimensions: list[str] = []
    for ac_id, body in criterion_rows:
        covers_match = re.search(r"`?Covers:\s*([^`\n]+)`?", body)
        if not covers_match:
            errors.append(f"{ac_id} has no Covers mapping")
            continue
        mapped = set(re.findall(r"REQ-[A-Za-z0-9_-]+", covers_match.group(1)))
        unknown = mapped - requirements
        if unknown:
            errors.append(f"{ac_id} covers unknown requirements: {', '.join(sorted(unknown))}")
        covered |= mapped & requirements
        dimension_matches = DIMENSION_RE.findall(body)
        if len(dimension_matches) != 1:
            errors.append(f"{ac_id} must declare exactly one Verification dimension")
        else:
            dimensions.append(dimension_matches[0])
        if len(re.findall(r"`Covers:", body)) != 1:
            errors.append(f"{ac_id} must declare exactly one Covers mapping")
    duplicate_dimensions = sorted(
        identity for identity, count in Counter(dimensions).items() if count > 1
    )
    if duplicate_dimensions:
        errors.append(
            "verification dimensions must be unique across atomic ACs: "
            + ", ".join(duplicate_dimensions)
        )
    for requirement in sorted(requirements - covered):
        errors.append(f"{requirement} is not covered by any AC")
    return sorted(set(errors))


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?m)^##\s+{re.escape(heading)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end():]
    boundary = re.search(r"(?m)^##\s+", tail)
    return tail[:boundary.start() if boundary else None].strip()


def validate_ready_coherence(spec: str) -> list[str]:
    errors: list[str] = []
    readiness = section(spec, "Readiness Decision")
    decision = re.findall(r"(?mi)^-\s+\*\*Decision:\*\*\s+`(DRAFT|READY)`\s*$", readiness)
    blockers = re.findall(r"(?mi)^-\s+\*\*Blocking reasons:\*\*\s+`([^`]+)`\s*$", readiness)
    if decision != ["READY"]:
        errors.append("Readiness Decision must contain exactly Decision READY")
    if len(blockers) != 1 or blockers[0].strip().casefold() != "none":
        errors.append("Readiness Decision READY requires exact Blocking reasons none")
    open_questions = section(spec, "Open Questions")
    if open_questions.strip().casefold() not in {"none", "none."}:
        errors.append("READY Open Questions must be exact None")
    client = section(spec, "Client Readiness")
    rows = []
    for line in client.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0].casefold() == "check" or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(cells)
    required_checks = {"Happy path", "Secondary states", "Product intent parity", "Atomic evidence obligations"}
    if {row[0] for row in rows} != required_checks:
        errors.append("Client Readiness must contain exact shared-contract completeness checks")
    for check, ios, android, evidence in rows:
        if ios != "PASS" or android != "PASS":
            errors.append(f"Client Readiness {check} must be PASS for iOS and Android")
        if not substantive(evidence, 5):
            errors.append(f"Client Readiness {check} requires product-contract evidence")
    readiness_surface = "\n".join((client, open_questions, readiness))
    readiness_surface = re.sub(r"(?mi)^\|\s*Check\s*\|.*$", "", readiness_surface)
    if re.search(r"\b(?:DRAFT|PENDING|GAP|UNKNOWN)\b", readiness_surface, re.I):
        errors.append("READY readiness surfaces contain contradictory non-ready claims")
    return errors


def validate_product_language(repo: Path, package: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(package.glob("*.md")):
        if path.name == "SPECIFICATION.md":
            continue
        errors.extend(artifact_language.validate_authored_markdown_language(repo, package, path))
    return errors


def validate_receipt_data(
    repo: Path, feature: str, receipt: dict[str, object]
) -> tuple[dict[str, object], list[str]]:
    subject = snapshot_product(repo, feature)
    errors: list[str] = []
    if set(receipt) != RECEIPT_KEYS:
        return subject, ["review receipt schema must be exact"]
    if receipt.get("schema_version") != 1 or receipt.get("feature") != feature:
        errors.append("review receipt identity/schema mismatch")
    if receipt.get("subject_fingerprint") != subject["fingerprint"]:
        errors.append("review receipt fingerprint is stale")
    if receipt.get("coordinator_role") != "elaborate-coordinator":
        errors.append("review receipt must be coordinator-owned")
    if receipt.get("lens_order") != list(LENSES):
        errors.append("review receipt lens order/set mismatch")
    if receipt.get("aggregate_status") not in {"PASS", "GAPS", "UNKNOWN"}:
        errors.append("review receipt aggregate_status is invalid")
    verdicts = receipt.get("verdicts")
    if not isinstance(verdicts, list):
        errors.append("review receipt verdicts must be an array")
    else:
        expected, aggregate_errors = aggregate_data(repo, feature, verdicts)
        errors.extend(aggregate_errors)
        if expected is not None and expected != receipt:
            errors.append("review receipt is not the exact deterministic aggregate")
    if receipt.get("aggregate_status") != "PASS":
        errors.append("review receipt aggregate_status must be PASS for readiness")
    return subject, sorted(set(errors))


def check_product(repo: Path, feature: str) -> list[str]:
    package = package_path(repo, feature)
    spec_path = package / "spec.md"
    spec = spec_path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    critical_fields = (
        "Status", "Product approval", "Approved by", "Approval evidence",
        "Applies to", "Source brief", "UX artifact", "Product review receipt",
        "UX readiness",
    )
    metadata, metadata_errors = exact_metadata(spec, critical_fields)
    errors.extend(metadata_errors)
    if metadata.get("Status") != "READY":
        errors.append("product Status must be READY")
    if metadata.get("Product approval") != "APPROVED":
        errors.append("Product approval must be APPROVED")
    if not substantive(metadata.get("Approved by"), 5):
        errors.append("Approved by must identify the human approver")
    if not substantive(metadata.get("Approval evidence"), 8):
        errors.append("Approval evidence must record the explicit human decision")
    else:
        errors.extend(artifact_language.validate_authored_json_string(
            metadata.get("Approval evidence"), "product Approval evidence"
        ))
    if metadata.get("Applies to") not in {"iOS, Android", "Android, iOS"}:
        errors.append("product spec must apply to both iOS and Android")
    if metadata.get("Source brief") != "brief.md":
        errors.append("Source brief must be exactly brief.md")
    elif not (package / "brief.md").is_file() or (package / "brief.md").is_symlink():
        errors.append("Source brief brief.md is missing or invalid")
    if metadata.get("Product review receipt") != "review-verdicts.json":
        errors.append("product spec must contain the static review-verdicts.json receipt reference")
    if metadata.get("UX readiness") != "review-verdicts.json#ux-accessibility":
        errors.append("product spec must link UX readiness to the receipt lens")
    errors.extend(requirement_coverage(spec))
    errors.extend(validate_ready_coherence(spec))
    errors.extend(validate_product_language(repo, package))
    receipt_path = package / "review-verdicts.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        errors.append("fresh product review receipt is missing")
        return sorted(set(errors))
    try:
        receipt = load_json_file(receipt_path, "product review receipt")
        _subject, receipt_errors = validate_receipt_data(repo, feature, receipt)
        errors.extend(receipt_errors)
    except ProductSpecError as error:
        errors.append(str(error))
        return sorted(set(errors))
    verdict_by_lens = {
        str(item.get("lens")): item
        for item in receipt.get("verdicts", []) if isinstance(item, dict)
    }
    ux_artifact = metadata.get("UX artifact", "")
    ux_verdict = verdict_by_lens.get("ux-accessibility", {})
    if ux_artifact == "ux.md":
        if not (package / "ux.md").is_file():
            errors.append("UX artifact ux.md is missing")
        if ux_verdict.get("applicability") != "REQUIRED" or ux_verdict.get("verdict") != "PASS":
            errors.append("UI/interaction package requires PASS ux-accessibility lens")
    elif ux_artifact.startswith("NOT APPLICABLE:"):
        ux_rationale = ux_artifact.partition(":")[2]
        if not substantive(ux_rationale, 12):
            errors.append("UX NOT APPLICABLE requires substantive rationale")
        else:
            errors.extend(artifact_language.validate_authored_json_string(
                ux_rationale, "product UX NOT APPLICABLE rationale"
            ))
        if ux_verdict.get("applicability") != "NOT_APPLICABLE" or ux_verdict.get("verdict") != "N/A":
            errors.append("non-UI package requires coherent ux-accessibility N/A verdict")
    else:
        errors.append("UX artifact must be ux.md or NOT APPLICABLE with rationale")
    return sorted(set(errors))


def fixture_spec(status: str = "DRAFT", approval: str = "APPROVED") -> str:
    return (
        "# Sample — shared product specification\n\n"
        f"- **Status:** `{status}`\n"
        f"- **Product approval:** `{approval}`\n"
        "- **Approved by:** Владелец продукта\n"
        "- **Approval evidence:** Явное одобрение зафиксировано в решении PRD-42\n"
        "- **Applies to:** `iOS, Android`\n"
        "- **Source brief:** `brief.md`\n"
        "- **UX artifact:** `NOT APPLICABLE: пользовательский интерфейс и взаимодействие не меняются`\n"
        "- **Product review receipt:** `review-verdicts.json`\n"
        "- **UX readiness:** `review-verdicts.json#ux-accessibility`\n\n"
        "## Requirements\n- `REQ-1` — Общее поведение остаётся наблюдаемым.\n\n"
        "## Acceptance Criteria\n- `AC-1` — Общее поведение наблюдается. `Covers: REQ-1` `Verification dimension: primary-outcome`\n\n"
        "## Client Readiness\n\n"
        "| Check | iOS | Android | Evidence or gap |\n|---|---|---|---|\n"
        "| Happy path | PASS | PASS | Полнота общего happy path подтверждена контрактом. |\n"
        "| Secondary states | PASS | PASS | Применимые вторичные состояния перечислены в контракте. |\n"
        "| Product intent parity | PASS | PASS | Единый продуктовый замысел задан для обоих клиентов. |\n"
        "| Atomic evidence obligations | PASS | PASS | Каждый AC имеет отдельную dimension проверки. |\n\n"
        "## Open Questions\nNone.\n\n"
        "## Readiness Decision\n- **Decision:** `READY`\n- **Blocking reasons:** `none`\n"
    )


def fixture_verdict(subject: dict[str, object], lens: str, index: int) -> dict[str, object]:
    optional = lens not in ALWAYS_REQUIRED
    applicability = "NOT_APPLICABLE" if optional else "REQUIRED"
    decision = "N/A" if optional else "PASS"
    return {
        "schema_version": 1,
        "feature": subject["feature"],
        "lens": lens,
        "subject_fingerprint": subject["fingerprint"],
        "reviewer_role": "product-spec-reviewer",
        "runtime": "codex",
        "run_id": f"review-run-{index:02d}",
        "parent_context_id": "elaborate-parent-session-01",
        "context_id": f"fresh-context-{index:02d}",
        "provenance_ref": f"codex:invocation/review-{index:02d}",
        "independent_context": True,
        "applicability": applicability,
        "verdict": decision,
        "clients_checked": ["iOS", "Android"],
        "rationale": (
            "В пакете нет применимого поведения для этой необязательной линзы."
            if optional else "Общий продуктовый контракт полон для обоих клиентов."
        ),
        "evidence_refs": ["spec.md"],
        "findings": [],
    }


def write_fixture(repo: Path) -> tuple[Path, dict[str, object], list[dict[str, object]]]:
    package = repo / "specs/product/sample"; package.mkdir(parents=True)
    (package / "brief.md").write_text("Содержательный общий продуктовый brief для обоих клиентов.\n", encoding="utf-8")
    (package / "spec.md").write_text(fixture_spec(), encoding="utf-8")
    subject = snapshot_product(repo, "sample")
    verdicts = [fixture_verdict(subject, lens, index) for index, lens in enumerate(LENSES, 1)]
    return package, subject, verdicts


def write_fixture_receipt(repo: Path, feature: str) -> Path:
    """Test support: create a valid receipt for the fixture's current subject."""
    subject = snapshot_product(repo, feature)
    verdicts = [fixture_verdict(subject, lens, index) for index, lens in enumerate(LENSES, 1)]
    receipt, errors = aggregate_data(repo, feature, verdicts)
    if errors or receipt is None:
        raise AssertionError(errors)
    return write_receipt(repo, feature, receipt)


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package, subject, verdicts = write_fixture(repo)
        before = snapshot_product(repo, "sample")
        for verdict in verdicts:
            assert validate_verdict_data(verdict, subject) == []
        assert snapshot_product(repo, "sample") == before
        self_authored = dict(verdicts[0]); self_authored["reviewer_role"] = "specification-writer"
        assert any("not the author" in item for item in validate_verdict_data(self_authored, subject))
        empty_pass = dict(verdicts[0], rationale="", evidence_refs=[])
        assert any("every verdict" in item for item in validate_verdict_data(empty_pass, subject))
        one_context = [dict(item, context_id="shared-context-01") for item in verdicts]
        assert any("one review context" in item for item in aggregate_data(repo, "sample", one_context)[1])
        mixed_parent = [dict(item) for item in verdicts]
        mixed_parent[-1]["parent_context_id"] = "different-parent-session-02"
        assert any("one parent coordinator" in item for item in aggregate_data(repo, "sample", mixed_parent)[1])
        duplicate_run = [dict(item) for item in verdicts]; duplicate_run[1]["run_id"] = duplicate_run[0]["run_id"]
        assert any("unique run_id" in item for item in aggregate_data(repo, "sample", duplicate_run)[1])
        stale = dict(verdicts[0]); stale["subject_fingerprint"] = "sha256:" + "0" * 64
        assert any("stale or mixed" in item for item in validate_verdict_data(stale, subject))
        assert aggregate_data(repo, "sample", verdicts[:-1])[0] is None
        duplicate_lens = [dict(item) for item in verdicts]; duplicate_lens[-1]["lens"] = "product"
        assert aggregate_data(repo, "sample", duplicate_lens)[0] is None
        product_na = dict(verdicts[0], applicability="NOT_APPLICABLE", verdict="N/A")
        assert any("always REQUIRED" in item for item in validate_verdict_data(product_na, subject))
        cross_na = dict(verdicts[-1], applicability="NOT_APPLICABLE", verdict="N/A")
        assert any("always REQUIRED" in item for item in validate_verdict_data(cross_na, subject))
        no_reason = dict(verdicts[1], rationale="none", evidence_refs=[])
        assert any("package-derived" in item for item in validate_verdict_data(no_reason, subject))
        blocker = dict(verdicts[0]); blocker["findings"] = [{
            "id": "finding-product-01", "severity": "blocker",
            "summary": "A blocking product contradiction remains.",
            "evidence": "spec.md requirements contradict acceptance behavior.",
            "requirement_ids": ["REQ-1"],
        }]
        assert any("PASS cannot" in item for item in validate_verdict_data(blocker, subject))
        fallback = dict(
            verdicts[0], independent_context=False,
            context_id=verdicts[0]["parent_context_id"],
        )
        assert any("same-context fallback" in item for item in validate_verdict_data(fallback, subject))
        fallback["verdict"] = "UNKNOWN"; fallback["rationale"] = "Независимый контекст reviewer недоступен в этом runtime."
        fallback["findings"] = [{
            "id": "finding-runtime-01", "severity": "blocker",
            "summary": "Независимый контекст не удалось создать.",
            "evidence": "Runtime предоставил для этого review только контекст автора.",
            "requirement_ids": [],
        }]
        assert validate_verdict_data(fallback, subject) == []
        unknown_receipt, unknown_errors = aggregate_data(repo, "sample", [fallback] + verdicts[1:])
        assert unknown_errors == [] and unknown_receipt and unknown_receipt["aggregate_status"] == "UNKNOWN"
        write_receipt(repo, "sample", unknown_receipt)
        assert any("aggregate_status must be PASS" in item for item in check_product(repo, "sample"))
        external = dict(
            verdicts[0], runtime="external", provenance_ref="external:manual-review-01"
        )
        assert any("explicit external-evidence" in item for item in validate_verdict_data(external, subject))
        external.update({
            "independent_context": False,
            "context_id": external["parent_context_id"],
            "verdict": "UNKNOWN",
            "rationale": "Для этой проверки недоступно подтверждение независимого внешнего вызова.",
            "findings": [{
                "id": "finding-external-01", "severity": "blocker",
                "summary": "Происхождение внешнего вызова не подтверждено.",
                "evidence": "У координатора нет явного подтверждения внешнего вызова.",
                "requirement_ids": [],
            }],
        })
        assert validate_verdict_data(external, subject) == []
        only_ios = dict(verdicts[0], clients_checked=["iOS"])
        assert any("both clients" in item for item in validate_verdict_data(only_ios, subject))
        gap = dict(verdicts[0], verdict="GAP", rationale="Деталь платформенной реализации попала в продуктовое поведение.")
        gap["findings"] = [{
            "id": "finding-platform-01", "severity": "major",
            "summary": "Продуктовая спецификация содержит решение платформенной реализации.",
            "evidence": "В spec.md назван клиентский фреймворк вместо наблюдаемого поведения.",
            "requirement_ids": ["REQ-1"],
        }]
        assert validate_verdict_data(gap, subject) == []
        gap_receipt, gap_errors = aggregate_data(repo, "sample", [gap] + verdicts[1:])
        assert gap_errors == [] and gap_receipt and gap_receipt["aggregate_status"] == "GAPS"
        write_receipt(repo, "sample", gap_receipt)
        assert any("aggregate_status must be PASS" in item for item in check_product(repo, "sample"))

        original = snapshot_product(repo, "sample")["fingerprint"]
        durable = package / "SPECIFICATION.md"
        durable.write_text("# Действующий доставленный контракт\n", encoding="utf-8")
        assert snapshot_product(repo, "sample")["fingerprint"] == original
        durable.write_text("# Обновлённый доставленный контракт\n", encoding="utf-8")
        assert snapshot_product(repo, "sample")["fingerprint"] == original
        durable.unlink()
        unknown = package / "notes.bin"; unknown.write_bytes(b"normative unknown input")
        added = snapshot_product(repo, "sample")["fingerprint"]; assert added != original
        unknown.write_bytes(b"changed normative input")
        changed = snapshot_product(repo, "sample")["fingerprint"]; assert changed != added
        unknown.unlink(); assert snapshot_product(repo, "sample")["fingerprint"] == original
        spec = package / "spec.md"; draft = spec.read_text(encoding="utf-8")
        spec.write_text(draft.replace("`DRAFT`", "`READY`", 1), encoding="utf-8")
        assert snapshot_product(repo, "sample")["fingerprint"] == original
        spec.write_text(draft.replace("Владелец продукта", "Другой владелец продукта"), encoding="utf-8")
        assert snapshot_product(repo, "sample")["fingerprint"] != original
        spec.write_text(draft, encoding="utf-8")

        spec.write_text(draft + "- **Status:** `DRAFT`\n", encoding="utf-8")
        try:
            snapshot_product(repo, "sample")
            raise AssertionError("duplicate exact Status metadata accepted")
        except ProductSpecError as error:
            assert "exactly one exact Status" in str(error)
        spec.write_text(draft, encoding="utf-8")

        receipt, errors = aggregate_data(repo, "sample", verdicts); assert errors == [] and receipt
        write_receipt(repo, "sample", receipt)
        assert snapshot_product(repo, "sample")["fingerprint"] == original
        assert any("Status must be READY" in item for item in check_product(repo, "sample"))
        spec.write_text(draft.replace("`DRAFT`", "`READY`", 1), encoding="utf-8")
        ready_errors = check_product(repo, "sample")
        assert ready_errors == [], ready_errors
        coherent_ready = spec.read_text(encoding="utf-8")
        spec.write_text(
            coherent_ready.replace("- **Decision:** `READY`", "- **Decision:** `DRAFT`"),
            encoding="utf-8",
        )
        contradictory_errors = check_product(repo, "sample")
        assert any("Readiness Decision" in item for item in contradictory_errors)
        spec.write_text(coherent_ready, encoding="utf-8")
        spec.write_text(
            coherent_ready.replace(
                "Явное одобрение зафиксировано в решении PRD-42",
                "This approval evidence is written as an English narrative.",
            ),
            encoding="utf-8",
        )
        approval_language_errors = check_product(repo, "sample")
        assert any("Approval evidence" in item and "Russian" in item for item in approval_language_errors)
        spec.write_text(
            coherent_ready.replace(
                "пользовательский интерфейс и взаимодействие не меняются",
                "the user interface and interaction do not change",
            ),
            encoding="utf-8",
        )
        ux_language_errors = check_product(repo, "sample")
        assert any("UX NOT APPLICABLE rationale" in item for item in ux_language_errors)
        spec.write_text(coherent_ready, encoding="utf-8")
        spec.write_text(spec.read_text(encoding="utf-8") + "\nNormative change.\n", encoding="utf-8")
        assert any("fingerprint is stale" in item for item in check_product(repo, "sample"))

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package, _subject, _verdicts = write_fixture(repo)
        spec = package / "spec.md"
        spec.write_text(fixture_spec(approval="PENDING"), encoding="utf-8")
        pending_subject = snapshot_product(repo, "sample")
        pending_verdicts = [fixture_verdict(pending_subject, lens, index) for index, lens in enumerate(LENSES, 1)]
        spec.write_text(fixture_spec(), encoding="utf-8")
        assert aggregate_data(repo, "sample", pending_verdicts)[0] is None
        spec.write_text(fixture_spec(status="READY"), encoding="utf-8")
        assert any("receipt is missing" in item for item in check_product(repo, "sample"))

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package, subject, verdicts = write_fixture(repo)
        spec = package / "spec.md"; spec.write_text(fixture_spec().replace("`Covers: REQ-1`", "No mapping"), encoding="utf-8")
        broken_subject = snapshot_product(repo, "sample")
        broken_verdicts = [fixture_verdict(broken_subject, lens, index) for index, lens in enumerate(LENSES, 1)]
        receipt, errors = aggregate_data(repo, "sample", broken_verdicts); assert not errors and receipt
        write_receipt(repo, "sample", receipt)
        spec.write_text(spec.read_text(encoding="utf-8").replace("`DRAFT`", "`READY`", 1), encoding="utf-8")
        assert any("Covers" in item or "not covered" in item for item in check_product(repo, "sample"))

    duplicate_req_errors = requirement_coverage(
        fixture_spec() + "\n- `REQ-1` — Conflicting duplicate requirement.\n"
    )
    assert any("duplicate REQ IDs" in item for item in duplicate_req_errors)
    duplicate_ac_errors = requirement_coverage(
        fixture_spec() + "\n- `AC-1` — Противоречащий дубликат. `Covers: REQ-1` `Verification dimension: duplicate`\n"
    )
    assert any("duplicate AC IDs" in item for item in duplicate_ac_errors)
    duplicate_dimension_errors = requirement_coverage(
        fixture_spec()
        + "\n- `AC-2` — Второй outcome ошибочно использует ту же dimension. "
          "`Covers: REQ-1` `Verification dimension: primary-outcome`\n"
    )
    assert any("verification dimensions must be unique" in item for item in duplicate_dimension_errors)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package, _subject, _verdicts = write_fixture(repo)
        write_fixture_receipt(repo, "sample")
        spec = package / "spec.md"
        ready = spec.read_text(encoding="utf-8").replace("`DRAFT`", "`READY`", 1)
        spec.write_text(
            ready
            + "\n- **Product approval:** `PENDING`\n"
            + "- **Source brief:** `conflicting-brief.md`\n",
            encoding="utf-8",
        )
        duplicate_metadata_errors = check_product(repo, "sample")
        assert any("Product approval metadata must appear exactly once" in item for item in duplicate_metadata_errors)
        assert any("Source brief metadata must appear exactly once" in item for item in duplicate_metadata_errors)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package, _subject, _verdicts = write_fixture(repo)
        link = package / "linked.md"; link.symlink_to(package / "brief.md")
        try:
            snapshot_product(repo, "sample")
            raise AssertionError("product symlink accepted")
        except ProductSpecError as error:
            assert "symlink" in str(error)
        try:
            snapshot_product(repo, "../escape")
            raise AssertionError("unsafe feature accepted")
        except ProductSpecError:
            pass
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); actual = repo / "actual-package"; actual.mkdir()
        (actual / "spec.md").write_text(fixture_spec(), encoding="utf-8")
        link = repo / "specs/product/sample"; link.parent.mkdir(parents=True); link.symlink_to(actual, target_is_directory=True)
        try:
            snapshot_product(repo, "sample")
            raise AssertionError("product package root symlink accepted")
        except ProductSpecError as error:
            assert "root symlink" in str(error)
    print("validate-product-spec self-test: PASS (fingerprint, isolated lenses, receipt, readiness, pressure)")
    return 0


def emit(value: object, as_json: bool = True) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path)
    subparsers = parser.add_subparsers(dest="command")
    snapshot_parser = subparsers.add_parser("snapshot"); snapshot_parser.add_argument("--feature", required=True)
    verdict_parser = subparsers.add_parser("validate-verdict"); verdict_parser.add_argument("--feature", required=True); verdict_parser.add_argument("--verdict", type=Path, required=True)
    aggregate_parser = subparsers.add_parser("aggregate"); aggregate_parser.add_argument("--feature", required=True); aggregate_parser.add_argument("--verdict", action="append", type=Path, required=True); aggregate_parser.add_argument("--write", action="store_true")
    check_parser = subparsers.add_parser("check"); check_parser.add_argument("--feature", required=True)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    repo = repository_root(args.root)
    try:
        if args.command == "snapshot":
            emit(snapshot_product(repo, args.feature)); return 0
        if args.command == "validate-verdict":
            verdict, errors = validate_verdict_file(repo, args.feature, args.verdict)
            emit({"status": "PASS" if not errors else "FAIL", "verdict": verdict, "errors": errors})
            return 0 if not errors else 2
        if args.command == "aggregate":
            verdicts = [load_json_file(path, "review verdict") for path in args.verdict]
            receipt, errors = aggregate_data(repo, args.feature, verdicts)
            if errors:
                emit({"status": "DRAFT", "errors": errors}); return 2
            target = write_receipt(repo, args.feature, receipt) if args.write else None
            aggregate_status = str(receipt["aggregate_status"])
            emit({"status": aggregate_status, "receipt": receipt, "written": target.relative_to(repo).as_posix() if target else None})
            return 0 if aggregate_status == "PASS" else 2
        if args.command == "check":
            errors = check_product(repo, args.feature)
            emit({"status": "PASS" if not errors else "DRAFT", "errors": errors})
            return 0 if not errors else 2
        parser.error("snapshot, validate-verdict, aggregate, check or --self-test is required")
    except (OSError, ProductSpecError) as error:
        emit({"status": "FAIL", "errors": [str(error)]}); return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
