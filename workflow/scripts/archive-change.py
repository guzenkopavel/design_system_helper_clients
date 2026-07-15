#!/usr/bin/env python3
"""Collision-safe dry-run/apply archive for implementation and product packages."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path


def load_validator():
    path = Path(__file__).with_name("validate-platform-change.py")
    spec = importlib.util.spec_from_file_location("archive_platform_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load platform validator")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def non_placeholder(value: object, minimum: int = 5) -> bool:
    text = str(value or "").strip()
    return len(text) >= minimum and not re.search(r"<[^>]+>|\b(?:TODO|TBD|UNKNOWN)\b", text, re.I)


def create_parent_tree(path: Path) -> list[Path]:
    created: list[Path] = []
    current = path
    while not current.exists():
        created.append(current)
        current = current.parent
    path.mkdir(parents=True, exist_ok=True)
    return created


def cleanup_created_dirs(created: list[Path]) -> None:
    for path in created:
        try:
            path.rmdir()
        except OSError:
            pass


def tree_signature(root: Path) -> list[tuple[str, str, str]]:
    signature: list[tuple[str, str, str]] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            signature.append(("dir", relative, ""))
        elif path.is_file():
            signature.append(("file", relative, hashlib.sha256(path.read_bytes()).hexdigest()))
    return signature


def archive_integrity(archive: Path) -> tuple[dict[str, str], str]:
    files: dict[str, str] = {}
    for path in sorted(archive.rglob("*")):
        if path.is_file() and path.name != "archive-receipt.json":
            files[path.relative_to(archive).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return files, hashlib.sha256(encoded).hexdigest()


def create_implementation_receipt(repo: Path, archive: Path, meta: dict[str, object]) -> dict[str, object]:
    state_path = archive / str(meta.get("verification_state", ""))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    files, digest = archive_integrity(archive)
    return {
        "schema_version": 1,
        "mode": "implementation",
        "platform": meta.get("platform"),
        "feature": meta.get("feature"),
        "change_id": meta.get("change_id"),
        "archived_at": meta.get("archived_at"),
        "archived_path": meta.get("archived_path"),
        "tasks_total": meta.get("tasks_total"),
        "tasks_done": meta.get("tasks_done"),
        "verification_status": meta.get("verification_status"),
        "verification_state": {
            "path": meta.get("verification_state"),
            "fingerprint": state.get("fingerprint"),
        },
        "integrity": {"algorithm": "sha256", "files": files, "digest": digest},
    }


def validate_implementation_receipt(
    repo: Path, receipt_path: Path, feature: str, platform: str
) -> list[str]:
    errors: list[str] = []
    try:
        relative = receipt_path.relative_to(repo)
    except ValueError:
        return [f"{platform} archive receipt escapes repository root"]
    parts = relative.parts
    if (
        len(parts) != 6
        or parts[0].casefold() != platform.casefold()
        or parts[1] != "specs"
        or parts[2] != feature
        or parts[3] != "archive"
        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*", parts[4])
        or parts[5] != "archive-receipt.json"
    ):
        return [
            f"{platform} archived evidence must be "
            f"<Platform>/specs/{feature}/archive/<archive-id>/archive-receipt.json"
        ]
    if not receipt_path.is_file():
        return [f"{platform} implementation archive receipt does not exist: {relative}"]
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"{platform} archive receipt JSON is invalid: {error}"]
    archive = receipt_path.parent
    meta_path = archive / "meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{platform} archived meta is missing or invalid: {error}"]
    expected_archive_path = archive.relative_to(repo).as_posix()
    checks = {
        "schema_version": 1,
        "mode": "implementation",
        "feature": feature,
        "archived_path": expected_archive_path,
        "verification_status": "PASS",
    }
    for field, expected in checks.items():
        if receipt.get(field) != expected:
            errors.append(f"{platform} receipt {field} mismatch")
    if str(receipt.get("platform", "")).casefold() != platform.casefold():
        errors.append(f"{platform} receipt platform mismatch")
    if not non_placeholder(receipt.get("change_id")):
        errors.append(f"{platform} receipt change_id missing")
    if not non_placeholder(receipt.get("archived_at"), 8):
        errors.append(f"{platform} receipt archived_at missing")
    total = receipt.get("tasks_total"); done = receipt.get("tasks_done")
    if not isinstance(total, int) or total <= 0 or done != total:
        errors.append(f"{platform} receipt requires tasks_total == tasks_done > 0")
    for field in ("platform", "feature", "change_id", "archived_at", "archived_path", "tasks_total", "tasks_done", "verification_status"):
        if meta.get(field) != receipt.get(field):
            errors.append(f"{platform} archived meta/receipt mismatch: {field}")
    if meta.get("status") != "archived":
        errors.append(f"{platform} archived meta status must be archived")
    state_ref = receipt.get("verification_state")
    if not isinstance(state_ref, dict):
        errors.append(f"{platform} receipt verification_state is invalid")
    else:
        raw_state_path = state_ref.get("path")
        if not isinstance(raw_state_path, str):
            errors.append(f"{platform} receipt verification state path missing")
        else:
            value = Path(raw_state_path); state_path = (archive / value).resolve()
            if value.is_absolute() or ".." in value.parts or archive not in state_path.parents or not state_path.is_file():
                errors.append(f"{platform} receipt verification state path unsafe/missing")
            else:
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as error:
                    errors.append(f"{platform} verification state JSON invalid: {error}")
                else:
                    if state.get("fingerprint") != state_ref.get("fingerprint") or meta.get("verification_state") != raw_state_path:
                        errors.append(f"{platform} verification state fingerprint/path mismatch")
    integrity = receipt.get("integrity")
    files, digest = archive_integrity(archive)
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "sha256":
        errors.append(f"{platform} receipt integrity schema invalid")
    elif integrity.get("files") != files or integrity.get("digest") != digest:
        errors.append(f"{platform} archive integrity mismatch")
    return errors


def implementation_preflight(root: Path, platform: str, feature: str, change: str | None) -> tuple[dict[str, object], str, Path, Path, list[str]]:
    validator = load_validator(); repo = root.resolve()
    adapter = validator.load_adapter(repo, platform)
    change_id, package = validator.resolve_change(repo, adapter, feature, change, "archive")
    errors = validator.validate_package(repo, adapter, feature, change_id, "archive")
    archive_id = f"{date.today().isoformat()}-{change_id}"
    package_root = validator.safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    target = package_root / feature / str(adapter["archive_namespace"]) / archive_id
    tombstone = package / "ARCHIVED.md"
    if target.exists(): errors.append(f"archive collision: {target.relative_to(repo)}")
    if tombstone.exists(): errors.append("implementation tombstone already exists")
    if package.exists() and not package.is_dir(): errors.append("active package is not a directory")
    if (package / "provenance/shared-product-spec.md").exists(): errors.append("shared product archive provenance already exists")
    if (package / "archive-receipt.json").exists(): errors.append("archive receipt must not exist in active package")
    return adapter, change_id, package, target, errors


def archive_implementation(root: Path, platform: str, feature: str, change: str | None, apply: bool, _fault: str | None = None) -> tuple[str, list[str]]:
    validator = load_validator(); repo = root.resolve()
    try:
        adapter, change_id, package, target, errors = implementation_preflight(repo, platform, feature, change)
    except (ValueError, OSError) as error:
        return "BLOCKED", [str(error)]
    if errors: return "BLOCKED", errors
    if not apply:
        return "DRY-RUN", [f"would move {package.relative_to(repo)} to {target.relative_to(repo)} and leave ARCHIVED.md"]
    meta_path = package / "meta.json"; original_meta = meta_path.read_bytes()
    meta = json.loads(original_meta)
    moved = False
    created_dirs: list[Path] = []
    try:
        created_dirs = create_parent_tree(target.parent)
        if _fault == "pre-move": raise OSError("injected before move")
        shutil.move(str(package), str(target)); moved = True
        if _fault == "post-move": raise OSError("injected after move")
        archived_meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
        archived_meta.update(status="archived", archived_at=now_iso(), archived_path=target.relative_to(repo).as_posix())
        (target / "meta.json").write_text(json.dumps(archived_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shared = archived_meta.get("shared_product_spec")
        if archived_meta.get("change_type") == "product-backed":
            if not isinstance(shared, str): raise ValueError("product-backed package has no shared spec")
            source = validator.safe_repo_path(repo, shared, "shared_product_spec")
            provenance = target / "provenance/shared-product-spec.md"
            provenance.parent.mkdir(parents=True, exist_ok=False)
            shutil.copy2(source, provenance)
        if _fault == "state-check": raise OSError("injected during archived state check")
        state_errors = validator.validate_state(repo, adapter, target, archived_meta)
        if state_errors:
            raise ValueError(f"archived verification state mismatch: {'; '.join(state_errors)}")
        receipt = create_implementation_receipt(repo, target, archived_meta)
        receipt_path = target / "archive-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if _fault == "receipt": raise OSError("injected during receipt creation")
        receipt_errors = validate_implementation_receipt(repo, receipt_path, feature, str(adapter["platform_name"]).casefold())
        if receipt_errors:
            raise ValueError(f"archive receipt validation failed: {'; '.join(receipt_errors)}")
        package.mkdir(parents=True, exist_ok=False)
        (package / "ARCHIVED.md").write_text(
            f"# Archived implementation change\n\n- Platform: {adapter['platform_name']}\n- Feature: {feature}\n- Change ID: {change_id}\n- Target: `{target.relative_to(repo).as_posix()}`\n- Archived at: {archived_meta['archived_at']}\n",
            encoding="utf-8",
        )
    except Exception as error:
        if moved:
            if package.exists(): shutil.rmtree(package)
            if target.exists(): shutil.move(str(target), str(package))
        if package.exists():
            (package / "meta.json").write_bytes(original_meta)
            receipt = package / "archive-receipt.json"
            if receipt.exists(): receipt.unlink()
            provenance = package / "provenance/shared-product-spec.md"
            if provenance.exists(): provenance.unlink()
            provenance_dir = package / "provenance"
            if provenance_dir.exists(): provenance_dir.rmdir()
        cleanup_created_dirs(created_dirs)
        return "BLOCKED", [f"archive rolled back: {error}"]
    return "APPLIED", [f"archived at {target.relative_to(repo)}; tombstone {package.relative_to(repo) / 'ARCHIVED.md'}"]


def parse_applies_to(spec_text: str) -> set[str]:
    match = re.search(r"(?mi)^-\s*\**Applies to\s*:\**\s*`?([^`\n]+)`?\s*$", spec_text)
    return {item.strip().casefold() for item in match.group(1).split(",") if item.strip()} if match else set()


def tombstone_fields(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for name in ("Platform", "Feature", "Change ID", "Target"):
        match = re.search(rf"(?mi)^-\s*{re.escape(name)}:\s*`?([^`\n]+)`?\s*$", text)
        if match:
            fields[name] = match.group(1).strip()
    return fields


def active_product_references(repo: Path, feature: str) -> list[str]:
    validator = load_validator()
    expected = f"specs/product/{feature}/spec.md"
    refs: list[str] = []
    roots: set[tuple[Path, str, str, str]] = set()
    for conventional in repo.glob("*/specs"):
        if conventional.is_dir():
            roots.add((conventional.resolve(), "changes", "archive", conventional.parent.name))
    for contract in sorted(repo.glob("*/workflow/platform-contract.json")):
        try:
            data = json.loads(contract.read_text(encoding="utf-8"))
            package_root = validator.safe_repo_path(repo, str(data.get("package_root", "")), "package_root")
            active_namespace = str(data.get("active_changes_namespace", "changes"))
            archive_namespace = str(data.get("archive_namespace", "archive"))
            if not validator.SLUG_RE.fullmatch(active_namespace) or not validator.SLUG_RE.fullmatch(archive_namespace):
                refs.append(f"invalid active namespace in adapter: {contract.relative_to(repo)}")
                continue
            platform_name = str(data.get("platform_name") or package_root.parts[-2])
            roots.add((package_root, active_namespace, archive_namespace, platform_name))
        except (ValueError, json.JSONDecodeError) as error:
            refs.append(f"invalid adapter during product reference scan: {contract.relative_to(repo)}: {error}")
    seen_namespaces: set[Path] = set()
    for package_root, active_namespace, archive_namespace, platform_name in sorted(roots, key=lambda item: str(item[0])):
        namespace = package_root / feature / active_namespace
        if namespace in seen_namespaces:
            continue
        seen_namespaces.add(namespace)
        if not namespace.exists():
            continue
        if not namespace.is_dir():
            refs.append(f"active namespace is not a directory: {namespace.relative_to(repo)}")
            continue
        for package in sorted(namespace.iterdir()):
            relative = package.relative_to(repo)
            if not package.is_dir():
                refs.append(f"unexpected entry under active changes: {relative}")
                continue
            entries = sorted(item.name for item in package.iterdir())
            meta_path = package / "meta.json"
            tombstone = package / "ARCHIVED.md"
            if meta_path.is_file():
                if tombstone.exists():
                    refs.append(f"active package mixes meta and tombstone: {relative}")
                    continue
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    refs.append(f"invalid active package meta: {meta_path.relative_to(repo)}")
                    continue
                if meta.get("status") == "archived":
                    refs.append(f"inconsistent archived meta under active changes: {relative}")
                elif meta.get("shared_product_spec") == expected:
                    refs.append(relative.as_posix())
                continue
            if entries != ["ARCHIVED.md"] or not tombstone.is_file():
                refs.append(f"partial or invalid active package: {relative}")
                continue
            fields = tombstone_fields(tombstone)
            if set(fields) != {"Platform", "Feature", "Change ID", "Target"}:
                refs.append(f"invalid implementation tombstone fields: {relative}")
                continue
            change_id = fields["Change ID"]
            target_value = fields["Target"]
            try:
                target = validator.safe_repo_path(repo, target_value, "tombstone target")
            except ValueError as error:
                refs.append(f"invalid implementation tombstone target: {relative}: {error}")
                continue
            expected_parent = package_root / feature / archive_namespace
            archive_id = target.name
            if (
                fields["Feature"] != feature
                or fields["Platform"].casefold() != platform_name.casefold()
                or target.parent != expected_parent
                or not re.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(change_id)}", archive_id)
            ):
                refs.append(f"implementation tombstone identity mismatch: {relative}")
                continue
            receipt_path = target / "archive-receipt.json"
            receipt_errors = validate_implementation_receipt(repo, receipt_path, feature, platform_name)
            if receipt_errors:
                refs.append(f"invalid implementation tombstone receipt: {relative}: {'; '.join(receipt_errors)}")
                continue
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("change_id") != change_id:
                refs.append(f"implementation tombstone change_id mismatch: {relative}")
    return refs


def validate_archived_disposition(
    repo: Path, feature: str, platform: str, evidence: object
) -> list[str]:
    validator = load_validator()
    if not isinstance(evidence, str) or not non_placeholder(evidence, 8):
        return [f"archived disposition for {platform} requires an implementation archive path"]
    try:
        target = validator.safe_repo_path(repo, evidence, f"{platform} archive evidence")
    except ValueError as error:
        return [str(error)]
    return validate_implementation_receipt(repo, target, feature, platform)


def product_preflight(root: Path, feature: str, request_path: Path | None) -> tuple[Path, Path, Path, dict[str, object], list[str]]:
    validator = load_validator(); repo = root.resolve(); errors: list[str] = []
    if not validator.SLUG_RE.fullmatch(feature):
        raise ValueError("feature must be strict kebab-case")
    source = repo / "specs/product" / feature
    spec_path = source / "spec.md"
    if not spec_path.is_file(): errors.append("active product spec is missing")
    request = request_path or source / "archive-request.json"
    if not request.is_absolute(): request = repo / request
    try:
        request = validator.safe_repo_path(repo, request.relative_to(repo).as_posix(), "archive request")
    except ValueError as error:
        errors.append(str(error))
    data: dict[str, object] = {}
    if not request.is_file(): errors.append(f"archive request is missing: {request}")
    else:
        try: data = json.loads(request.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error: errors.append(f"archive request JSON invalid: {error}")
    reason = data.get("reason")
    if data.get("feature") != feature: errors.append("archive request feature mismatch")
    if reason not in {"completed", "superseded", "cancelled"}: errors.append("archive reason must be completed, superseded or cancelled")
    approval = data.get("retirement_approval")
    if not isinstance(approval, dict) or not non_placeholder(approval.get("approved_by")) or not non_placeholder(approval.get("evidence"), 8):
        errors.append("explicit retirement approver and evidence are required")
    platforms = data.get("platforms")
    if not isinstance(platforms, dict):
        platforms = {}; errors.append("platform dispositions object is required")
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else ""
    applies = parse_applies_to(spec_text)
    if reason == "completed" and spec_text:
        if validator.field_value(spec_text, "Status") != "READY":
            errors.append("completed product archive requires active product Status READY")
        if validator.field_value(spec_text, "Product approval") != "APPROVED":
            errors.append("completed product archive requires Product approval APPROVED")
        if not validator.valid_human(validator.field_value(spec_text, "Approved by")):
            errors.append("completed product archive requires concrete Approved by")
        if not validator.valid_human(validator.field_value(spec_text, "Approval evidence"), 8):
            errors.append("completed product archive requires concrete Approval evidence")
    required = applies | {"ios", "android"}
    for platform in sorted(required):
        entry = platforms.get(platform)
        if not isinstance(entry, dict):
            errors.append(f"missing explicit disposition for {platform}"); continue
        disposition = entry.get("disposition")
        if disposition not in {"archived", "cancelled", "not-applicable"}: errors.append(f"invalid disposition for {platform}")
        if disposition == "archived":
            errors.extend(validate_archived_disposition(repo, feature, platform, entry.get("evidence")))
        elif not non_placeholder(entry.get("evidence"), 8):
            errors.append(f"missing disposition evidence for {platform}")
        if reason == "completed" and platform in applies and disposition != "archived": errors.append(f"completed requires archived disposition for {platform}")
    for ref in active_product_references(repo, feature): errors.append(f"active implementation reference blocks product archive: {ref}")
    archive_id = f"{date.today().isoformat()}-{feature}"
    target = repo / "specs/product/_archive" / feature / archive_id
    if target.exists(): errors.append(f"product archive collision: {target.relative_to(repo)}")
    return source, target, request, data, errors


def archive_product(root: Path, feature: str, request_path: Path | None, apply: bool, _fault: str | None = None) -> tuple[str, list[str]]:
    repo = root.resolve()
    try: source, target, _request, data, errors = product_preflight(repo, feature, request_path)
    except (ValueError, OSError) as error: return "BLOCKED", [str(error)]
    if errors: return "BLOCKED", errors
    if not apply: return "DRY-RUN", [f"would move {source.relative_to(repo)} to {target.relative_to(repo)} and leave spec.md tombstone"]
    moved = False
    created_dirs: list[Path] = []
    try:
        created_dirs = create_parent_tree(target.parent)
        if _fault == "pre-move": raise OSError("injected before move")
        shutil.move(str(source), str(target)); moved = True
        if _fault == "post-move": raise OSError("injected after move")
        source.mkdir(parents=True, exist_ok=False)
        approval = data["retirement_approval"]
        (source / "spec.md").write_text(
            "# Archived product package\n\n"
            "- **Status:** `ARCHIVED`\n"
            f"- **Reason:** `{data['reason']}`\n"
            f"- **Archive target:** `{target.relative_to(repo).as_posix()}`\n"
            f"- **Retirement approved by:** `{approval['approved_by']}`\n"
            f"- **Retirement approval evidence:** `{approval['evidence']}`\n"
            f"- **Archived at:** `{now_iso()}`\n",
            encoding="utf-8",
        )
    except Exception as error:
        if moved:
            if source.exists(): shutil.rmtree(source)
            if target.exists(): shutil.move(str(target), str(source))
        cleanup_created_dirs(created_dirs)
        return "BLOCKED", [f"product archive rolled back: {error}"]
    return "APPLIED", [f"product archived at {target.relative_to(repo)}; exact-path tombstone retained"]


def terminal_fixture(repo: Path):
    validator = load_validator(); _adapter, _package, meta = validator.write_fixture(repo)
    (repo / "TestClient").rename(repo / "iOS")
    adapter_path = repo / "iOS/workflow/platform-contract.json"
    adapter_data = json.loads(adapter_path.read_text(encoding="utf-8"))
    adapter_data.update(
        platform_input="ios", platform_name="iOS", platform_root="iOS",
        package_root="iOS/specs", production_roots=["iOS"],
        protected_roots=["iOS/specs", "iOS/workflow"],
        production_exclusions=["iOS/specs", "iOS/workflow"],
        rule_files=["iOS/workflow/rule.md"],
    )
    adapter_path.write_text(json.dumps(adapter_data), encoding="utf-8")
    adapter = validator.load_adapter(repo, "ios")
    package = repo / "iOS/specs/sample/changes/sample"
    meta["platform"] = "iOS"
    product = repo / "specs/product/sample/spec.md"
    product.write_text(product.read_text().replace("`TestClient`", "`iOS, Android`"))
    plan = package / "plan"; plan.mkdir()
    (plan / "README.md").write_text("# Plan\n\n## Planning frame\nOne bounded task follows approved contracts.\n\n## DAG\ntask-001 is ready without dependencies.\n\n## Estimates and multipliers\nGreenfield uncertainty is included in the range.\n\n## Verification strategy\nRun a focused check and record evidence.\n")
    source = repo / "iOS/Sources/Sample.swift"; source.parent.mkdir(parents=True); source.write_text("struct Sample {}\n")
    task = "# task-001\n- Layer: domain\n- Depends on: none\n- Status: done\n- Evidence: evidence/task-001.md\n- Estimate (ideal): 0.5–1 days\n- Paths: existing: iOS/Sources/Sample.swift\n\n## Goal\nImplement the typed platform boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the result.\n\n## Steps\nCreate the typed boundary with focused verification.\n\n## Verification\nRun the deterministic boundary test.\n\n## Expected result\nThe boundary test records a passing result.\n\n## Out of scope\nOther features and cleanup remain excluded.\n"
    (plan / "task-001.md").write_text(task)
    evidence = package / "evidence"; evidence.mkdir(); (evidence / "task-001.md").write_text("Focused test PASS.\n")
    for name in ("req","ac","preq","pac"): (evidence/f"{name}.md").write_text("Fresh PASS evidence.\n")
    (package/"verification.md").write_text("# Verification\n\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run current shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | PASS |\n")
    meta.update(status="verified", tasks_total=1, tasks_done=1, verification_status="PASS", verified_at="2026-07-15T12:00:00Z", verification_state="evidence/verification-state.json")
    state=validator.compute_state(repo, adapter, package, meta); state["captured_at"]="2026-07-15T12:00:00Z"
    (evidence/"verification-state.json").write_text(json.dumps(state))
    (package/"meta.json").write_text(json.dumps(meta))
    return package


def clone_terminal_android(repo: Path) -> Path:
    validator = load_validator()
    shutil.copytree(repo / "iOS", repo / "Android")
    adapter_path = repo / "Android/workflow/platform-contract.json"
    adapter_data = json.loads(adapter_path.read_text(encoding="utf-8"))
    adapter_data.update(
        platform_input="android", platform_name="Android", platform_root="Android",
        package_root="Android/specs", production_roots=["Android"],
        protected_roots=["Android/specs", "Android/workflow"],
        production_exclusions=["Android/specs", "Android/workflow"],
        rule_files=["Android/workflow/rule.md"],
    )
    adapter_path.write_text(json.dumps(adapter_data), encoding="utf-8")
    package = repo / "Android/specs/sample/changes/sample"
    meta_path = package / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")); meta["platform"] = "Android"
    task_path = package / "plan/task-001.md"
    task_path.write_text(task_path.read_text(encoding="utf-8").replace("iOS/", "Android/"), encoding="utf-8")
    adapter = validator.load_adapter(repo, "android")
    state = validator.compute_state(repo, adapter, package, meta); state["captured_at"] = "2026-07-15T12:00:00Z"
    (package / "evidence/verification-state.json").write_text(json.dumps(state), encoding="utf-8")
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return package


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package = terminal_fixture(repo); android_package = clone_terminal_android(repo)
        request = repo / "specs/product/sample/archive-request.json"
        request.write_text(json.dumps({"feature":"sample","reason":"completed","retirement_approval":{"approved_by":"Product owner","evidence":"retirement decision record"},"platforms":{"ios":{"disposition":"archived","evidence":"implementation archive record"},"android":{"disposition":"archived","evidence":"implementation archive record"}}}))
        alt_contract = repo / "Alt/workflow/platform-contract.json"; alt_contract.parent.mkdir(parents=True)
        alt_contract.write_text(json.dumps({"package_root":"Nonstandard/platform-packages","active_changes_namespace":"cycles"}))
        alt_active = repo / "Nonstandard/platform-packages/sample/cycles/alt/meta.json"; alt_active.parent.mkdir(parents=True)
        alt_active.write_text(json.dumps({"status":"implementing","shared_product_spec":"specs/product/sample/spec.md"}))
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("Nonstandard/platform-packages" in error for error in errors)
        shutil.rmtree(alt_active.parent)
        status, _ = archive_implementation(repo, "ios", "sample", "sample", False); assert status == "DRY-RUN"
        before_implementation = tree_signature(repo)
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="pre-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="post-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="state-check")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="receipt")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True); assert status == "APPLIED"
        assert (package / "ARCHIVED.md").is_file()
        status, _ = archive_implementation(repo, "android", "sample", "sample", True); assert status == "APPLIED"
        assert (android_package / "ARCHIVED.md").is_file()
        # Product disposition validation is receipt-based and does not need a live adapter.
        (repo / "Android/workflow/platform-contract.json").unlink()
        inconsistent = repo / "Android/specs/sample/changes/stale/meta.json"; inconsistent.parent.mkdir(parents=True)
        inconsistent.write_text(json.dumps({"platform":"Android","feature":"sample","status":"archived","shared_product_spec":"specs/product/sample/spec.md"}))
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("inconsistent archived meta" in error for error in errors)
        inconsistent.unlink()
        inconsistent.parent.rmdir()
        partial = repo / "Android/specs/sample/changes/partial"; partial.mkdir()
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("partial or invalid active package" in error for error in errors)
        partial.rmdir()
        extra = repo / "Android/specs/sample/changes/extra"; extra.mkdir()
        (extra / "ARCHIVED.md").write_text("# Invalid\n", encoding="utf-8")
        (extra / "extra.txt").write_text("unexpected\n", encoding="utf-8")
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("partial or invalid active package" in error for error in errors)
        shutil.rmtree(extra)
        invalid_tombstone = repo / "Android/specs/sample/changes/invalid"; invalid_tombstone.mkdir()
        (invalid_tombstone / "ARCHIVED.md").write_text(
            "# Archived\n\n- Platform: Android\n- Feature: sample\n- Change ID: invalid\n- Target: `../../escape`\n",
            encoding="utf-8",
        )
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("invalid implementation tombstone target" in error for error in errors)
        shutil.rmtree(invalid_tombstone)
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("archived evidence" in error for error in errors)
        ios_archive = repo / f"iOS/specs/sample/archive/{date.today().isoformat()}-sample/archive-receipt.json"
        android_archive = repo / f"Android/specs/sample/archive/{date.today().isoformat()}-sample/archive-receipt.json"
        assert ios_archive.is_file() and android_archive.is_file()
        request_data = json.loads(request.read_text())
        request_data["platforms"]["ios"]["evidence"] = ios_archive.relative_to(repo).as_posix()
        request_data["platforms"]["android"]["evidence"] = android_archive.relative_to(repo).as_posix()
        request.write_text(json.dumps(request_data))
        request_data["platforms"]["ios"]["evidence"] = "../../escape"
        request.write_text(json.dumps(request_data))
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("safe repo-relative" in error for error in errors)
        request_data["platforms"]["ios"]["evidence"] = package.relative_to(repo).as_posix()
        request.write_text(json.dumps(request_data))
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("archive-receipt.json" in error for error in errors)
        fake_archive = repo / "iOS/specs/sample/archive/2026-01-01-fake"
        fake_archive.mkdir()
        (fake_archive / "meta.json").write_text(json.dumps({"status":"archived"}), encoding="utf-8")
        (fake_archive / "archive-receipt.json").write_text(json.dumps({"schema_version":1}), encoding="utf-8")
        request_data["platforms"]["ios"]["evidence"] = (fake_archive / "archive-receipt.json").relative_to(repo).as_posix()
        request.write_text(json.dumps(request_data))
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("receipt" in error for error in errors)
        shutil.rmtree(fake_archive)
        request_data["platforms"]["ios"]["evidence"] = ios_archive.relative_to(repo).as_posix()
        request.write_text(json.dumps(request_data))
        product = repo / "specs/product/sample/spec.md"
        ready_product = product.read_text()
        draft_product = ready_product.replace("`READY`", "`DRAFT`").replace("`APPROVED`", "`PENDING`")
        product.write_text(draft_product)
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("requires active product Status READY" in error for error in errors)
        request_data["reason"] = "cancelled"
        request.write_text(json.dumps(request_data))
        status, _ = archive_product(repo, "sample", request, False); assert status == "DRY-RUN"
        request_data["reason"] = "completed"
        request.write_text(json.dumps(request_data))
        product.write_text(ready_product)
        status, _ = archive_product(repo, "sample", request, False); assert status == "DRY-RUN"
        before_product = tree_signature(repo)
        status, _ = archive_product(repo, "sample", request, True, _fault="pre-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, _ = archive_product(repo, "sample", request, True, _fault="post-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, _ = archive_product(repo, "sample", request, True); assert status == "APPLIED"
        assert (repo / "specs/product/sample/spec.md").is_file()
        assert "ARCHIVED" in (repo / "specs/product/sample/spec.md").read_text()
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("collision" in error for error in errors)
        status, _ = archive_product(repo, "../escape", None, False); assert status == "BLOCKED"
    print("archive-change self-test: PASS (implementation/product gates, isolation, collision safety)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("implementation", "product"))
    parser.add_argument("--platform"); parser.add_argument("--feature"); parser.add_argument("--change")
    parser.add_argument("--request", type=Path); parser.add_argument("--apply", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]); parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test: return self_test()
    if not args.mode or not args.feature: parser.error("mode and --feature are required")
    if args.mode == "implementation":
        if not args.platform: parser.error("implementation mode requires --platform")
        status, details = archive_implementation(args.root, args.platform, args.feature, args.change, args.apply)
    else:
        status, details = archive_product(args.root, args.feature, args.request, args.apply)
    print(f"Archive {args.mode}: {status}")
    for detail in details: print(f"- {detail}")
    return 0 if status in {"DRY-RUN", "APPLIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
