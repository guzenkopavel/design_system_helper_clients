#!/usr/bin/env python3
"""Collision-safe dry-run/apply archive for implementation and product packages."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import artifact_language


DURABLE_SPECIFICATION = "SPECIFICATION.md"


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


def directory_chain_errors(repo: Path, path: Path, label: str) -> list[str]:
    """Validate an existing/missing directory chain lexically without following links."""
    try:
        relative = path.relative_to(repo)
    except ValueError:
        return [f"{label} escapes repository root"]
    current = repo
    for component in relative.parts:
        current = current / component
        if not os.path.lexists(current):
            continue
        try:
            mode = current.lstat().st_mode
        except OSError as error:
            return [f"{label} cannot be inspected: {error}"]
        if stat.S_ISLNK(mode):
            return [f"{label} has a symlink ancestor: {current.relative_to(repo)}"]
        if not stat.S_ISDIR(mode):
            return [f"{label} has a non-directory ancestor: {current.relative_to(repo)}"]
    return []


def create_parent_tree(repo: Path, path: Path, label: str) -> list[Path]:
    errors = directory_chain_errors(repo, path, label)
    if errors:
        raise ValueError("; ".join(errors))
    created: list[Path] = []
    current = path
    while not os.path.lexists(current):
        created.append(current)
        current = current.parent
    path.mkdir(parents=True, exist_ok=True)
    errors = directory_chain_errors(repo, path, label)
    if errors:
        raise ValueError("; ".join(errors))
    return created


def cleanup_created_dirs(created: list[Path]) -> None:
    for path in created:
        try:
            path.rmdir()
        except OSError:
            pass


def atomic_write_bytes(target: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        try:
            os.unlink(temporary)
        except OSError:
            pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def regular_file_or_absent(path: Path, label: str) -> list[str]:
    """Reject symlinks and non-regular collisions without following them."""
    if not os.path.lexists(path):
        return []
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        return [f"{label} cannot be inspected: {error}"]
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        return [f"{label} must be an absent or regular non-symlink file"]
    return []


def regular_file_errors(path: Path, label: str) -> list[str]:
    if not os.path.lexists(path):
        return [f"{label} does not exist"]
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        return [f"{label} cannot be inspected: {error}"]
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        return [f"{label} must be a regular non-symlink file"]
    return []


def regular_tree_errors(root: Path, label: str) -> list[str]:
    """Require a self-contained tree of real directories and regular files."""
    errors = directory_chain_errors(root.parent, root, label)
    if errors:
        return errors
    try:
        root_mode = root.lstat().st_mode
    except OSError as error:
        return [f"{label} cannot be inspected: {error}"]
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        return [f"{label} root must be a regular non-symlink directory"]
    for base, directories, filenames in os.walk(root, followlinks=False):
        directories.sort(); filenames.sort()
        for name in directories:
            path = Path(base) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                errors.append(f"{label} contains unsafe directory entry: {path.relative_to(root)}")
        for name in filenames:
            path = Path(base) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                errors.append(f"{label} contains unsafe file entry: {path.relative_to(root)}")
    return errors


def reject_symlink_ancestors(repo: Path, path: Path, label: str) -> list[str]:
    current = path.parent
    while current != repo:
        if os.path.lexists(current) and current.is_symlink():
            return [f"{label} has a symlink ancestor: {current.relative_to(repo)}"]
        if current.parent == current:
            return [f"{label} escapes repository root"]
        current = current.parent
    return []


def durable_specification_payload(
    *,
    kind: str,
    feature: str,
    source_path: str,
    source_payload: bytes,
    archive_path: str,
    evidence_path: str,
    platform: str | None = None,
    product_baseline_path: str | None = None,
) -> bytes:
    """Build a deterministic current baseline around an immutable archived source."""
    title = (
        f"# Текущая спецификация реализации {platform}: {feature}"
        if kind == "implementation"
        else f"# Текущая продуктовая спецификация: {feature}"
    )
    scope = f"- **Платформа:** `{platform}`\n" if platform else ""
    product_baseline = (
        f"- **Продуктовый baseline:** `{product_baseline_path}` — текущий продуктовый контракт после "
        "`archive product completed`; до его публикации общий контракт зафиксирован в provenance текущего archive.\n"
        if product_baseline_path else ""
    )
    header = (
        f"{title}\n\n"
        "## Происхождение baseline\n\n"
        f"- **Feature:** `{feature}`\n"
        f"{scope}"
        f"{product_baseline}"
        f"- **Источник:** `{source_path}`\n"
        f"- **SHA-256 источника:** `{sha256_bytes(source_payload)}`\n"
        f"- **Архив:** `{archive_path}`\n"
        f"- **Evidence:** `{evidence_path}`\n\n"
        "## Текущий доставленный контракт\n\n"
    ).encode("utf-8")
    return header + source_payload.lstrip(b"\xef\xbb\xbf\n")


def tree_signature(root: Path) -> list[tuple[str, str, str]]:
    signature: list[tuple[str, str, str]] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            signature.append(("symlink", relative, os.readlink(path)))
        elif stat.S_ISDIR(mode):
            signature.append(("dir", relative, ""))
        elif stat.S_ISREG(mode):
            signature.append(("file", relative, hashlib.sha256(path.read_bytes()).hexdigest()))
        else:
            signature.append(("special", relative, oct(stat.S_IFMT(mode))))
    return signature


def archive_integrity(archive: Path, *, ignore_ds_store: bool) -> tuple[dict[str, str], str]:
    tree_errors = regular_tree_errors(archive, "implementation archive")
    if tree_errors:
        raise ValueError("; ".join(tree_errors))
    files: dict[str, str] = {}
    for path in sorted(archive.rglob("*")):
        if stat.S_ISREG(path.lstat().st_mode) and path != archive / "archive-receipt.json":
            if ignore_ds_store and path.name == ".DS_Store":
                continue
            files[path.relative_to(archive).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return files, hashlib.sha256(encoded).hexdigest()


def create_implementation_receipt(
    repo: Path,
    archive: Path,
    meta: dict[str, object],
    durable_path: Path,
    durable_payload: bytes,
) -> dict[str, object]:
    state_path = archive / str(meta.get("verification_state", ""))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    files, digest = archive_integrity(archive, ignore_ds_store=True)
    return {
        "schema_version": 2,
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
        "durable_specification": {
            "path": durable_path.relative_to(repo).as_posix(),
            "source": (archive / "implementation-spec.md").relative_to(repo).as_posix(),
            "source_sha256": sha256_bytes((archive / "implementation-spec.md").read_bytes()),
            "published_sha256": sha256_bytes(durable_payload),
        },
        "integrity": {"algorithm": "sha256", "files": files, "digest": digest},
    }


def create_implementation_retirement_receipt(
    repo: Path,
    archive: Path,
    meta: dict[str, object],
    reason: str,
) -> dict[str, object]:
    files, digest = archive_integrity(archive, ignore_ds_store=True)
    return {
        "schema_version": 1,
        "mode": "implementation-retirement",
        "reason": reason,
        "platform": meta.get("platform"),
        "feature": meta.get("feature"),
        "change_id": meta.get("change_id"),
        "archived_at": meta.get("archived_at"),
        "archived_path": meta.get("archived_path"),
        "retired_status": meta.get("retired_status"),
        "tasks_total": meta.get("tasks_total"),
        "tasks_done": meta.get("tasks_done"),
        "verification_status": meta.get("verification_status"),
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
    archive = receipt_path.parent
    structural_errors = directory_chain_errors(repo, archive, f"{platform} implementation archive")
    if not structural_errors:
        structural_errors.extend(regular_tree_errors(archive, f"{platform} implementation archive"))
    if structural_errors:
        return structural_errors
    receipt_errors = regular_file_errors(receipt_path, f"{platform} implementation archive receipt")
    if receipt_errors:
        return receipt_errors
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{platform} archive receipt JSON is invalid: {error}"]
    meta_path = archive / "meta.json"
    meta_errors = regular_file_errors(meta_path, f"{platform} archived meta")
    if meta_errors:
        return meta_errors
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{platform} archived meta is missing or invalid: {error}"]
    expected_archive_path = archive.relative_to(repo).as_posix()
    checks = {
        "mode": "implementation",
        "feature": feature,
        "archived_path": expected_archive_path,
        "verification_status": "PASS",
    }
    for field, expected in checks.items():
        if receipt.get(field) != expected:
            errors.append(f"{platform} receipt {field} mismatch")
    schema_version = receipt.get("schema_version")
    if schema_version not in {1, 2}:
        errors.append(f"{platform} receipt schema_version mismatch")
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
            value = Path(raw_state_path); state_path = archive / value
            state_errors = regular_file_errors(state_path, f"{platform} verification state")
            if (
                value.is_absolute()
                or ".." in value.parts
                or archive not in state_path.parents
                or state_errors
            ):
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
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "sha256":
        errors.append(f"{platform} receipt integrity schema invalid")
    else:
        expected_files = integrity.get("files")
        v1_lists_ds_store = (
            schema_version == 1
            and isinstance(expected_files, dict)
            and any(Path(str(name)).name == ".DS_Store" for name in expected_files)
        )
        try:
            files, digest = archive_integrity(
                archive,
                ignore_ds_store=(schema_version == 2 or (schema_version == 1 and not v1_lists_ds_store)),
            )
        except ValueError as error:
            errors.append(f"{platform} archive integrity tree invalid: {error}")
        else:
            if expected_files != files or integrity.get("digest") != digest:
                errors.append(f"{platform} archive integrity mismatch")
    durable = receipt.get("durable_specification")
    if schema_version == 2 and (
        not isinstance(durable, dict)
        or set(durable) != {"path", "source", "source_sha256", "published_sha256"}
    ):
        errors.append(f"{platform} receipt durable specification binding is invalid")
    elif schema_version == 2 and isinstance(durable, dict):
        expected_path = archive.parents[1] / DURABLE_SPECIFICATION
        expected_source = archive / "implementation-spec.md"
        if durable.get("path") != expected_path.relative_to(repo).as_posix():
            errors.append(f"{platform} receipt durable specification path mismatch")
        if durable.get("source") != expected_source.relative_to(repo).as_posix():
            errors.append(f"{platform} receipt durable specification source mismatch")
        if regular_file_errors(expected_source, f"{platform} archived implementation specification"):
            errors.append(f"{platform} archived implementation specification is missing or unsafe")
        else:
            source_payload = expected_source.read_bytes()
            if durable.get("source_sha256") != sha256_bytes(source_payload):
                errors.append(f"{platform} receipt durable specification source hash mismatch")
            expected_payload = durable_specification_payload(
                kind="implementation",
                feature=feature,
                platform=str(receipt.get("platform")),
                source_path=expected_source.relative_to(repo).as_posix(),
                source_payload=source_payload,
                archive_path=archive.relative_to(repo).as_posix(),
                evidence_path=receipt_path.relative_to(repo).as_posix(),
                product_baseline_path=(
                    f"specs/product/{feature}/{DURABLE_SPECIFICATION}"
                    if meta.get("change_type") == "product-backed" else None
                ),
            )
            if durable.get("published_sha256") != sha256_bytes(expected_payload):
                errors.append(f"{platform} receipt durable specification published hash mismatch")
    return errors


def validate_implementation_retirement_receipt(
    repo: Path, receipt_path: Path, feature: str, platform: str
) -> list[str]:
    errors: list[str] = []
    try:
        relative = receipt_path.relative_to(repo)
    except ValueError:
        return [f"{platform} retirement receipt escapes repository root"]
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
            f"{platform} retired implementation evidence must be "
            f"<Platform>/specs/{feature}/archive/<archive-id>/archive-receipt.json"
        ]
    archive = receipt_path.parent
    structural_errors = directory_chain_errors(repo, archive, f"{platform} retired implementation archive")
    if not structural_errors:
        structural_errors.extend(regular_tree_errors(archive, f"{platform} retired implementation archive"))
    if structural_errors:
        return structural_errors
    receipt_errors = regular_file_errors(receipt_path, f"{platform} implementation retirement receipt")
    if receipt_errors:
        return receipt_errors
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{platform} retirement receipt JSON is invalid: {error}"]
    expected_keys = {
        "schema_version", "mode", "reason", "platform", "feature", "change_id",
        "archived_at", "archived_path", "retired_status", "tasks_total",
        "tasks_done", "verification_status", "integrity",
    }
    if set(receipt) != expected_keys:
        errors.append(f"{platform} retirement receipt schema must be exact")
    meta_path = archive / "meta.json"
    meta_errors = regular_file_errors(meta_path, f"{platform} retired archived meta")
    if meta_errors:
        return meta_errors
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{platform} retired archived meta is missing or invalid: {error}"]
    expected_archive_path = archive.relative_to(repo).as_posix()
    checks = {
        "schema_version": 1,
        "mode": "implementation-retirement",
        "feature": feature,
        "archived_path": expected_archive_path,
    }
    for field, expected in checks.items():
        if receipt.get(field) != expected:
            errors.append(f"{platform} retirement receipt {field} mismatch")
    if receipt.get("reason") not in {"superseded", "cancelled"}:
        errors.append(f"{platform} retirement receipt reason mismatch")
    if str(receipt.get("platform", "")).casefold() != platform.casefold():
        errors.append(f"{platform} retirement receipt platform mismatch")
    if not non_placeholder(receipt.get("change_id")):
        errors.append(f"{platform} retirement receipt change_id missing")
    if not non_placeholder(receipt.get("archived_at"), 8):
        errors.append(f"{platform} retirement receipt archived_at missing")
    if meta.get("status") != "archived":
        errors.append(f"{platform} retired meta status must be archived")
    if meta.get("retirement_reason") != receipt.get("reason"):
        errors.append(f"{platform} retired meta/receipt mismatch: retirement_reason")
    if meta.get("retired_status") != receipt.get("retired_status"):
        errors.append(f"{platform} retired meta/receipt mismatch: retired_status")
    if receipt.get("retired_status") not in {"specified", "planned", "implementing"}:
        errors.append(f"{platform} retirement receipt retired_status mismatch")
    for field in (
        "platform", "feature", "change_id", "archived_at", "archived_path",
        "tasks_total", "tasks_done", "verification_status",
    ):
        if meta.get(field) != receipt.get(field):
            errors.append(f"{platform} retired meta/receipt mismatch: {field}")
    total = receipt.get("tasks_total"); done = receipt.get("tasks_done")
    if not isinstance(total, int) or total < 0 or not isinstance(done, int) or done < 0 or done > total:
        errors.append(f"{platform} retirement receipt task counts are invalid")
    if receipt.get("verification_status") not in {"pending", "FAIL", "UNKNOWN"}:
        errors.append(f"{platform} retirement receipt verification_status mismatch")
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "sha256":
        errors.append(f"{platform} retirement receipt integrity schema invalid")
    else:
        try:
            files, digest = archive_integrity(archive, ignore_ds_store=True)
        except ValueError as error:
            errors.append(f"{platform} retired archive integrity tree invalid: {error}")
        else:
            if integrity.get("files") != files or integrity.get("digest") != digest:
                errors.append(f"{platform} retired archive integrity mismatch")
    return errors


def retirement_validation_mode(status: object) -> str | None:
    if status == "specified":
        return "propose"
    if status == "planned":
        return "plan"
    if status == "implementing":
        return "implement"
    return None


def implementation_preflight(
    root: Path,
    platform: str,
    feature: str,
    change: str | None,
    retire: str | None = None,
) -> tuple[dict[str, object], str, Path, Path, list[str]]:
    validator = load_validator(); repo = root.resolve()
    adapter = validator.load_adapter(repo, platform)
    validator.require_capability(adapter, "archive-implementation")
    change_id, package = validator.resolve_change(repo, adapter, feature, change, "archive")
    errors = regular_tree_errors(package, "active implementation package")
    if not errors:
        if retire is None:
            errors.extend(validator.validate_package(repo, adapter, feature, change_id, "archive"))
        else:
            try:
                meta = json.loads((package / "meta.json").read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                meta = {}; errors.append(f"active implementation meta is invalid: {error}")
            status = meta.get("status")
            mode = retirement_validation_mode(status)
            if mode is None:
                errors.append("implementation retirement requires specified, planned or implementing status")
            elif meta.get("verification_status") == "PASS" or status == "verified":
                errors.append("verified packages must use normal implementation archive")
            else:
                errors.extend(validator.validate_package(repo, adapter, feature, change_id, mode))
    archive_id = f"{date.today().isoformat()}-{change_id}"
    package_root = validator.safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    target = package_root / feature / str(adapter["archive_namespace"]) / archive_id
    tombstone = package / "ARCHIVED.md"
    if os.path.lexists(target): errors.append(f"archive collision: {target.relative_to(repo)}")
    errors.extend(directory_chain_errors(repo, target.parent, "implementation archive namespace"))
    if tombstone.exists(): errors.append("implementation tombstone already exists")
    if package.exists() and not package.is_dir(): errors.append("active package is not a directory")
    if (package / "provenance/shared-product-spec.md").exists(): errors.append("shared product archive provenance already exists")
    if (package / "archive-receipt.json").exists(): errors.append("archive receipt must not exist in active package")
    implementation_spec = package / "implementation-spec.md"
    if not implementation_spec.is_file() or implementation_spec.is_symlink():
        errors.append("implementation-spec.md must be a regular non-symlink file")
    if retire is None:
        durable_path = package_root / feature / DURABLE_SPECIFICATION
        errors.extend(regular_file_or_absent(durable_path, "durable platform specification"))
        errors.extend(reject_symlink_ancestors(repo, durable_path, "durable platform specification"))
    return adapter, change_id, package, target, errors


def archive_implementation(
    root: Path,
    platform: str,
    feature: str,
    change: str | None,
    apply: bool,
    retire: str | None = None,
    _fault: str | None = None,
) -> tuple[str, list[str]]:
    validator = load_validator(); repo = root.resolve()
    try:
        adapter, change_id, package, target, errors = implementation_preflight(repo, platform, feature, change, retire)
    except (ValueError, OSError) as error:
        return "BLOCKED", [str(error)]
    if retire is not None and retire not in {"superseded", "cancelled"}:
        errors.append("implementation retirement reason must be superseded or cancelled")
    if errors: return "BLOCKED", errors
    package_root = validator.safe_repo_path(repo, str(adapter["package_root"]), "package_root")
    durable_path = package_root / feature / DURABLE_SPECIFICATION
    if retire is not None:
        if not apply:
            return "DRY-RUN", [
                f"would retire {package.relative_to(repo)} as {retire}, move it to "
                f"{target.relative_to(repo)} and leave ARCHIVED.md without publishing "
                f"{durable_path.relative_to(repo)}"
            ]
        meta_path = package / "meta.json"; original_meta = meta_path.read_bytes()
        moved = False
        created_dirs: list[Path] = []
        try:
            created_dirs = create_parent_tree(repo, target.parent, "implementation archive namespace")
            if _fault == "pre-move": raise OSError("injected before move")
            shutil.move(str(package), str(target)); moved = True
            if _fault == "post-move": raise OSError("injected after move")
            archived_meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
            retired_status = archived_meta.get("status")
            archived_meta.update(
                status="archived",
                archived_at=now_iso(),
                archived_path=target.relative_to(repo).as_posix(),
                retirement_reason=retire,
                retired_status=retired_status,
            )
            (target / "meta.json").write_text(json.dumps(archived_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            receipt_path = target / "archive-receipt.json"
            receipt = create_implementation_retirement_receipt(repo, target, archived_meta, retire)
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if _fault == "receipt": raise OSError("injected during receipt creation")
            receipt_errors = validate_implementation_retirement_receipt(
                repo, receipt_path, feature, str(adapter["platform_name"]).casefold()
            )
            if receipt_errors:
                raise ValueError(f"retirement receipt validation failed: {'; '.join(receipt_errors)}")
            if _fault == "baseline-write": raise OSError("injected after retirement receipt")
            package.mkdir(parents=True, exist_ok=False)
            (package / "ARCHIVED.md").write_text(
                f"# Archived implementation change\n\n"
                f"- Platform: {adapter['platform_name']}\n"
                f"- Feature: {feature}\n"
                f"- Change ID: {change_id}\n"
                f"- Reason: {retire}\n"
                f"- Target: `{target.relative_to(repo).as_posix()}`\n"
                f"- Archived at: {archived_meta['archived_at']}\n",
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
            cleanup_created_dirs(created_dirs)
            return "BLOCKED", [f"implementation retirement rolled back: {error}"]
        return "APPLIED", [
            f"retired {package.relative_to(repo)} as {retire}; archived at {target.relative_to(repo)}; "
            f"tombstone {package.relative_to(repo) / 'ARCHIVED.md'}; durable specification unchanged"
        ]
    if not apply:
        return "DRY-RUN", [
            f"would publish {durable_path.relative_to(repo)}, move {package.relative_to(repo)} "
            f"to {target.relative_to(repo)} and leave ARCHIVED.md"
        ]
    meta_path = package / "meta.json"; original_meta = meta_path.read_bytes()
    meta = json.loads(original_meta)
    moved = False
    durable_touched = False
    prior_durable = durable_path.read_bytes() if durable_path.is_file() else None
    created_dirs: list[Path] = []
    try:
        created_dirs = create_parent_tree(repo, target.parent, "implementation archive namespace")
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
        receipt_path = target / "archive-receipt.json"
        archived_spec = target / "implementation-spec.md"
        durable_payload = durable_specification_payload(
            kind="implementation",
            feature=feature,
            platform=str(adapter["platform_name"]),
            source_path=archived_spec.relative_to(repo).as_posix(),
            source_payload=archived_spec.read_bytes(),
            archive_path=target.relative_to(repo).as_posix(),
            evidence_path=receipt_path.relative_to(repo).as_posix(),
            product_baseline_path=(
                f"specs/product/{feature}/{DURABLE_SPECIFICATION}"
                if archived_meta.get("change_type") == "product-backed" else None
            ),
        )
        receipt = create_implementation_receipt(repo, target, archived_meta, durable_path, durable_payload)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if _fault == "receipt": raise OSError("injected during receipt creation")
        receipt_errors = validate_implementation_receipt(repo, receipt_path, feature, str(adapter["platform_name"]).casefold())
        if receipt_errors:
            raise ValueError(f"archive receipt validation failed: {'; '.join(receipt_errors)}")
        atomic_write_bytes(durable_path, durable_payload); durable_touched = True
        if _fault == "baseline-write": raise OSError("injected after durable specification publication")
        package.mkdir(parents=True, exist_ok=False)
        (package / "ARCHIVED.md").write_text(
            f"# Archived implementation change\n\n- Platform: {adapter['platform_name']}\n- Feature: {feature}\n- Change ID: {change_id}\n- Target: `{target.relative_to(repo).as_posix()}`\n- Archived at: {archived_meta['archived_at']}\n",
            encoding="utf-8",
        )
    except Exception as error:
        if durable_touched:
            if prior_durable is None:
                durable_path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(durable_path, prior_durable)
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
    return "APPLIED", [
        f"published {durable_path.relative_to(repo)}; archived at {target.relative_to(repo)}; "
        f"tombstone {package.relative_to(repo) / 'ARCHIVED.md'}"
    ]


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
            retirement_errors = validate_implementation_retirement_receipt(repo, receipt_path, feature, platform_name)
            if receipt_errors and retirement_errors:
                refs.append(
                    f"invalid implementation tombstone receipt: {relative}: "
                    f"verified archive: {'; '.join(receipt_errors)}; "
                    f"retirement archive: {'; '.join(retirement_errors)}"
                )
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
    source_tree_errors = regular_tree_errors(source, "active product package")
    errors.extend(source_tree_errors)
    if source.is_symlink() or not source.is_dir():
        errors.append("active product package must be a regular non-symlink directory")
    spec_path = source / "spec.md"
    if not spec_path.is_file(): errors.append("active product spec is missing")
    if spec_path.is_symlink(): errors.append("active product spec must be a regular non-symlink file")
    errors.extend(regular_file_or_absent(source / DURABLE_SPECIFICATION, "durable product specification"))
    errors.extend(reject_symlink_ancestors(repo, source / DURABLE_SPECIFICATION, "durable product specification"))
    if os.path.lexists(source / "retirement-request.json"):
        errors.append("active product package contains reserved retirement-request.json")
    raw_request = request_path or Path(
        "specs/product/_retirement-requests"
    ) / feature / f"{date.today().isoformat()}-{feature}.json"
    if not raw_request.is_absolute() and ".." in raw_request.parts:
        errors.append("archive request must be a safe repo-relative path")
    request = raw_request if raw_request.is_absolute() else repo / raw_request
    try:
        request_relative = request.relative_to(repo)
        request_safe = True
    except ValueError:
        request_relative = None
        request_safe = False
        errors.append("archive request must be a safe repo-relative path")
    request_structure_errors = (
        directory_chain_errors(repo, request.parent, "archive request") if request_safe else []
    )
    errors.extend(request_structure_errors)
    if request == source or source in request.parents:
        errors.append("archive request must live outside the active product package")
    data: dict[str, object] = {}
    request_file_errors = (
        regular_file_errors(request, "archive request")
        if request_safe and not request_structure_errors else ["archive request path is unsafe"]
    )
    if request_file_errors:
        errors.extend(request_file_errors)
        errors.append(f"archive request is missing or unsafe: {request_relative or request}")
    else:
        try:
            if request.lstat().st_size > 1024 * 1024:
                raise ValueError("archive request exceeds 1 MiB bound")
            loaded = json.loads(request.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                errors.append("archive request JSON must be an object")
            else:
                data = loaded
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            errors.append(f"archive request JSON invalid: {error}")
    if data and set(data) != {"feature", "reason", "retirement_approval", "platforms"}:
        errors.append("archive request top-level schema must be exact")
    reason = data.get("reason")
    if data.get("feature") != feature: errors.append("archive request feature mismatch")
    if reason not in {"completed", "superseded", "cancelled"}: errors.append("archive reason must be completed, superseded or cancelled")
    approval = data.get("retirement_approval")
    if not isinstance(approval, dict) or not non_placeholder(approval.get("approved_by")) or not non_placeholder(approval.get("evidence"), 8):
        errors.append("explicit retirement approver and evidence are required")
    elif set(approval) != {"approved_by", "evidence"}:
        errors.append("retirement_approval schema must be exact")
    else:
        errors.extend(artifact_language.validate_authored_json_string(
            approval.get("evidence"), "retirement_approval.evidence"
        ))
    platforms = data.get("platforms")
    if not isinstance(platforms, dict):
        platforms = {}; errors.append("platform dispositions object is required")
    spec_text = spec_path.read_text(encoding="utf-8") if not source_tree_errors and spec_path.is_file() else ""
    applies = parse_applies_to(spec_text)
    if reason == "completed" and spec_text and not source_tree_errors:
        if validator.field_value(spec_text, "Status") != "READY":
            errors.append("completed product archive requires active product Status READY")
        if validator.field_value(spec_text, "Product approval") != "APPROVED":
            errors.append("completed product archive requires Product approval APPROVED")
        if not validator.valid_human(validator.field_value(spec_text, "Approved by")):
            errors.append("completed product archive requires concrete Approved by")
        if not validator.valid_human(validator.field_value(spec_text, "Approval evidence"), 8):
            errors.append("completed product archive requires concrete Approval evidence")
        errors.extend(
            f"completed product archive product review gate: {item}"
            for item in validator.validate_product_ready(repo, feature)
        )
    required = applies | {"ios", "android"}
    for platform in sorted(required):
        entry = platforms.get(platform)
        if not isinstance(entry, dict):
            errors.append(f"missing explicit disposition for {platform}"); continue
        if set(entry) != {"disposition", "evidence"}:
            errors.append(f"platform disposition schema must be exact for {platform}")
        disposition = entry.get("disposition")
        if disposition not in {"archived", "cancelled", "not-applicable"}: errors.append(f"invalid disposition for {platform}")
        if disposition == "archived":
            errors.extend(validate_archived_disposition(repo, feature, platform, entry.get("evidence")))
        elif not non_placeholder(entry.get("evidence"), 8):
            errors.append(f"missing disposition evidence for {platform}")
        elif disposition in {"cancelled", "not-applicable"}:
            errors.extend(artifact_language.validate_authored_json_string(
                entry.get("evidence"), f"platforms.{platform}.evidence"
            ))
        if reason == "completed" and platform in applies and disposition != "archived": errors.append(f"completed requires archived disposition for {platform}")
    for ref in active_product_references(repo, feature): errors.append(f"active implementation reference blocks product archive: {ref}")
    archive_id = f"{date.today().isoformat()}-{feature}"
    target = repo / "specs/product/_archive" / feature / archive_id
    if os.path.lexists(target): errors.append(f"product archive collision: {target.relative_to(repo)}")
    errors.extend(directory_chain_errors(repo, target.parent, "product archive namespace"))
    return source, target, request, data, errors


def archive_product(root: Path, feature: str, request_path: Path | None, apply: bool, _fault: str | None = None) -> tuple[str, list[str]]:
    repo = root.resolve()
    try: source, target, request, data, errors = product_preflight(repo, feature, request_path)
    except (ValueError, OSError) as error: return "BLOCKED", [str(error)]
    if errors: return "BLOCKED", errors
    reason = str(data.get("reason"))
    durable_path = source / DURABLE_SPECIFICATION
    if not apply:
        baseline_action = "publish current durable specification" if reason == "completed" else "preserve existing durable specification without promoting the retired candidate"
        return "DRY-RUN", [
            f"would {baseline_action}, move {source.relative_to(repo)} to {target.relative_to(repo)} "
            "and leave spec.md tombstone"
        ]
    request_payload = request.read_bytes()
    prior_durable = durable_path.read_bytes() if durable_path.is_file() else None
    moved = False
    created_dirs: list[Path] = []
    try:
        created_dirs = create_parent_tree(repo, target.parent, "product archive namespace")
        if _fault == "pre-move": raise OSError("injected before move")
        shutil.move(str(source), str(target)); moved = True
        if _fault == "post-move": raise OSError("injected after move")
        durable_request = target / "retirement-request.json"
        atomic_write_bytes(durable_request, request_payload)
        if _fault == "post-copy": raise OSError("injected after durable request copy")
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
        if reason == "completed":
            archived_spec = target / "spec.md"
            durable_payload = durable_specification_payload(
                kind="product",
                feature=feature,
                source_path=archived_spec.relative_to(repo).as_posix(),
                source_payload=archived_spec.read_bytes(),
                archive_path=target.relative_to(repo).as_posix(),
                evidence_path=durable_request.relative_to(repo).as_posix(),
            )
            atomic_write_bytes(durable_path, durable_payload)
        elif prior_durable is not None:
            atomic_write_bytes(durable_path, prior_durable)
        if _fault == "baseline-write": raise OSError("injected after durable product specification handling")
        if _fault == "tombstone-write": raise OSError("injected after tombstone write")
    except Exception as error:
        if moved:
            if source.exists(): shutil.rmtree(source)
            durable_request = target / "retirement-request.json"
            if durable_request.exists(): durable_request.unlink()
            for temporary in target.glob(".retirement-request.json-*.tmp"):
                temporary.unlink()
            if target.exists(): shutil.move(str(target), str(source))
        cleanup_created_dirs(created_dirs)
        return "BLOCKED", [f"product archive rolled back: {error}"]
    baseline_result = (
        f"current specification published at {durable_path.relative_to(repo)}"
        if reason == "completed"
        else "prior current specification preserved without candidate promotion"
    )
    return "APPLIED", [f"product archived at {target.relative_to(repo)}; {baseline_result}; exact-path tombstone retained"]


def terminal_fixture(repo: Path):
    validator = load_validator(); _adapter, _package, meta = validator.write_fixture(repo)
    (repo / "TestClient").rename(repo / "iOS")
    adapter_path = repo / "iOS/workflow/platform-contract.json"
    adapter_data = json.loads(adapter_path.read_text(encoding="utf-8"))
    adapter_data = json.loads(json.dumps(adapter_data).replace("TestClient/", "iOS/"))
    adapter_data.update(
        platform_input="ios", platform_name="iOS", platform_root="iOS",
        package_root="iOS/specs", production_roots=["iOS"],
        protected_roots=["iOS/specs", "iOS/workflow"],
        production_exclusions=["iOS/specs", "iOS/workflow"],
    )
    adapter_path.write_text(json.dumps(adapter_data), encoding="utf-8")
    adapter = validator.load_adapter(repo, "ios")
    package = repo / "iOS/specs/sample/changes/sample"
    for markdown in package.rglob("*.md"):
        markdown.write_text(
            markdown.read_text(encoding="utf-8").replace("TestClient/", "iOS/"),
            encoding="utf-8",
        )
    meta = json.loads(json.dumps(meta).replace("TestClient/", "iOS/")); meta["platform"] = "iOS"
    product = repo / "specs/product/sample/spec.md"
    product.write_text(product.read_text().replace("`TestClient`", "`iOS, Android`"))
    plan = package / "plan"; plan.mkdir()
    (plan / "README.md").write_text("# Plan\n\n## Planning frame\nOne bounded task follows approved contracts.\n\n## Revalidated engineering scopes and exact rules\n- Engineering scopes: [\"application\"]\n- Applicable rule files: [\"iOS/workflow/base.md\", \"iOS/workflow/application.md\"]\n\n## DAG\ntask-001 is ready without dependencies.\n\n## Estimates and multipliers\nGreenfield uncertainty is included in the range.\n\n## Verification strategy\nRun a focused check and record evidence.\n")
    source = repo / "iOS/Sources/Sample.swift"; source.parent.mkdir(parents=True); source.write_text("struct Sample {}\n")
    task = "# task-001\n- Layer: domain\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: done\n- Evidence: evidence/task-001.md\n- Estimate (ideal): 0.5–1 days\n- Paths: existing: iOS/Sources/Sample.swift\n\n## Goal\nImplement the typed platform boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the result.\n\n## Implementation deliverables\n- Typed platform behavior boundary in `Sample.swift`.\n- Focused behavior test for the deterministic result.\n\n## Steps\nCreate the typed boundary with focused verification.\n\n## Verification\nRun the deterministic boundary test.\n\n## Expected result\nThe boundary test records a passing result.\n\n## Out of scope\nOther features and cleanup remain excluded.\n"
    task = task.replace("- Layer: domain\n", "- Layer: domain\n- Boundary owner: Sample capability boundary\n", 1)
    (plan / "task-001.md").write_text(task)
    evidence = package / "evidence"; evidence.mkdir(); (evidence / "task-001.md").write_text("Focused test PASS.\n")
    for name in ("req","ac","preq","pac"): (evidence/f"{name}.md").write_text("Fresh PASS evidence.\n")
    (package/"verification.md").write_text(
        "# Verification\n\n" + validator.fixture_modularity_verification("PASS")
        + "\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run current shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | PASS |\n"
    )
    meta.update(status="verified", tasks_total=1, tasks_done=1, verification_status="PASS", verified_at="2026-07-15T12:00:00Z", verification_state="evidence/verification-state.json", rule_selection_snapshot="plan/rule-selection.json")
    (plan / "rule-selection.json").write_text(json.dumps(validator.rule_selection_snapshot(meta)))
    state=validator.compute_state(repo, adapter, package, meta); state["captured_at"]="2026-07-15T12:00:00Z"
    (evidence/"verification-state.json").write_text(json.dumps(state))
    (package/"meta.json").write_text(json.dumps(meta))
    return package


def terminal_android_fixture(repo: Path) -> Path:
    validator = load_validator()
    android = repo / "Android"
    workflow = android / "workflow"; workflow.mkdir(parents=True)
    adapter_data = {
        "platform_input": "android", "platform_name": "Android", "platform_root": "Android",
        "lifecycle_capabilities": ["propose", "plan", "implement", "verify", "archive-implementation"],
        "package_root": "Android/specs", "active_changes_namespace": "changes", "archive_namespace": "archive",
        "production_roots": ["Android"], "protected_roots": ["Android/specs", "Android/workflow"],
        "production_exclusions": ["Android/specs", "Android/workflow"], "contract_prefix": "AND",
        "boundary_guard": "android-boundary", "extended_design_sections": ["Android integration"],
        "ui_task_checks": ["emulator", "accessibility", "design-system"],
        "platform_ux": {
            "role": "android-ux-designer", "artifact": "platform-ux.md",
            "design_language": "Material 3", "required_terms": ["Material 3"],
            "task_checks": ["platform-ux.md", "Material 3"],
        },
        "modularity": {
            "contract_version": 1,
            "isolation_scope": "application",
            "platform_rule": "Android/workflow/application.md",
            "physical_units": ["Fixture Android library module"],
            "legacy_task_checks": ["application boundary"],
        },
        "rule_files": ["Android/workflow/base.md", "Android/workflow/application.md", "Android/workflow/ui.md"],
        "phase_rule_profiles": {
            "propose": ["Android/workflow/base.md"], "plan": ["Android/workflow/base.md"],
            "implement": ["Android/workflow/base.md"], "verify": ["Android/workflow/base.md"],
        },
        "scope_rule_profiles": {
            "application": ["Android/workflow/application.md"], "ui": ["Android/workflow/ui.md"],
        },
        "scope_task_checks": {"ui": ["emulator", "accessibility", "design-system"]},
        "context_file_suffixes": [".md", ".json", ".kt", ".kts"],
        "context_excluded_directories": [".gradle", "build"],
        "context_always_include_globs": ["Android/**/settings.gradle.kts", "Android/**/build.gradle.kts"],
        "pre_commit": {
            "source_suffixes": [".kt", ".kts"], "generated_globs": ["Android/**/build/**"],
            "secret_globs": ["Android/**/*.keystore"],
            "security_sensitive_globs": ["Android/**/build.gradle.kts"],
            "ui_globs": ["Android/**/*Screen.kt"], "localization_globs": ["Android/**/strings.xml"],
            "project_globs": ["Android/**/settings.gradle.kts", "Android/**/build.gradle.kts"],
            "tool_globs": {"gradle": ["Android/**/settings.gradle.kts"]},
        },
    }
    adapter_path = workflow / "platform-contract.json"
    adapter_path.write_text(json.dumps(adapter_data), encoding="utf-8")
    (workflow / "base.md").write_text("Android lifecycle base rule.\n", encoding="utf-8")
    (workflow / "application.md").write_text("Android application boundary rule.\n", encoding="utf-8")
    (workflow / "ui.md").write_text("Android UI verification rule.\n", encoding="utf-8")
    platform_verify = workflow / "phases/verify.md"; platform_verify.parent.mkdir(parents=True)
    platform_verify.write_text("Android terminal verification addendum.\n", encoding="utf-8")
    shutil.copytree(repo / "iOS/specs/sample", android / "specs/sample")
    (android / "settings.gradle.kts").write_text('rootProject.name = "fixture"\n', encoding="utf-8")
    (android / "build.gradle.kts").write_text("plugins {}\n", encoding="utf-8")
    source = android / "src/main/kotlin/Sample.kt"; source.parent.mkdir(parents=True)
    source.write_text("data class Sample(val value: String)\n", encoding="utf-8")
    package = repo / "Android/specs/sample/changes/sample"
    for markdown in package.rglob("*.md"):
        markdown.write_text(
            markdown.read_text(encoding="utf-8").replace("TST-", "AND-").replace("iOS/", "Android/"),
            encoding="utf-8",
        )
    meta_path = package / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta = json.loads(json.dumps(meta).replace("iOS/", "Android/")); meta["platform"] = "Android"
    task_path = package / "plan/task-001.md"
    task_path.write_text(
        task_path.read_text(encoding="utf-8").replace(
            "Android/Sources/Sample.swift", "Android/src/main/kotlin/Sample.kt"
        ),
        encoding="utf-8",
    )
    plan_index = package / "plan/README.md"
    plan_index.write_text(plan_index.read_text(encoding="utf-8").replace("iOS/", "Android/"), encoding="utf-8")
    adapter = validator.load_adapter(repo, "android")
    (package / "plan/rule-selection.json").write_text(json.dumps(validator.rule_selection_snapshot(meta)), encoding="utf-8")
    state = validator.compute_state(repo, adapter, package, meta); state["captured_at"] = "2026-07-15T12:00:00Z"
    (package / "evidence/verification-state.json").write_text(json.dumps(state), encoding="utf-8")
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return package


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); package = terminal_fixture(repo); android_package = terminal_android_fixture(repo)
        request = repo / "specs/product/_retirement-requests/sample" / f"{date.today().isoformat()}-sample.json"
        request.parent.mkdir(parents=True)
        request.write_text(json.dumps({"feature":"sample","reason":"completed","retirement_approval":{"approved_by":"Product owner","evidence":"явное решение о выводе продукта из эксплуатации"},"platforms":{"ios":{"disposition":"archived","evidence":"implementation archive record"},"android":{"disposition":"archived","evidence":"implementation archive record"}}}, ensure_ascii=False))
        product_validator = load_validator().load_product_validator()
        fingerprint_with_external_request = product_validator.snapshot_product(repo, "sample")["fingerprint"]
        product_validator.write_fixture_receipt(repo, "sample")
        assert product_validator.snapshot_product(repo, "sample")["fingerprint"] == fingerprint_with_external_request
        valid_request_payload = request.read_text(encoding="utf-8")
        request.write_text("[]\n", encoding="utf-8")
        malformed_status, malformed_errors = archive_product(repo, "sample", None, False)
        assert malformed_status == "BLOCKED" and any("must be an object" in error for error in malformed_errors)
        request.unlink()
        missing_status, missing_errors = archive_product(repo, "sample", None, False)
        assert missing_status == "BLOCKED" and any("archive request is missing" in error for error in missing_errors)
        request.write_text(valid_request_payload, encoding="utf-8")
        internal_request = repo / "specs/product/sample/internal-retirement-request.json"
        internal_request.write_text(valid_request_payload, encoding="utf-8")
        product_validator.write_fixture_receipt(repo, "sample")
        internal_fingerprint = product_validator.snapshot_product(repo, "sample")["fingerprint"]
        internal_tree = tree_signature(repo)
        internal_status, internal_errors = archive_product(repo, "sample", internal_request, False)
        assert internal_status == "BLOCKED" and any("outside the active product package" in error for error in internal_errors)
        assert product_validator.snapshot_product(repo, "sample")["fingerprint"] == internal_fingerprint
        assert tree_signature(repo) == internal_tree
        internal_request.unlink()
        product_validator.write_fixture_receipt(repo, "sample")
        english_request = json.loads(valid_request_payload)
        english_request["retirement_approval"]["evidence"] = "This retirement approval is written as English narrative evidence."
        request.write_text(json.dumps(english_request), encoding="utf-8")
        english_status, english_errors = archive_product(repo, "sample", None, False)
        assert english_status == "BLOCKED" and any("retirement_approval.evidence" in error for error in english_errors)
        request.write_text(valid_request_payload, encoding="utf-8")
        alt_contract = repo / "Alt/workflow/platform-contract.json"; alt_contract.parent.mkdir(parents=True)
        alt_contract.write_text(json.dumps({"package_root":"Nonstandard/platform-packages","active_changes_namespace":"cycles"}))
        alt_active = repo / "Nonstandard/platform-packages/sample/cycles/alt/meta.json"; alt_active.parent.mkdir(parents=True)
        alt_active.write_text(json.dumps({"status":"implementing","shared_product_spec":"specs/product/sample/spec.md"}))
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("Nonstandard/platform-packages" in error for error in errors)
        shutil.rmtree(alt_active.parent)
        with tempfile.TemporaryDirectory() as retire_tmp:
            retire_repo = Path(retire_tmp).resolve()
            retire_ios_package = terminal_fixture(retire_repo)
            retire_android_package = terminal_android_fixture(retire_repo)
            for retired_package in (retire_ios_package, retire_android_package):
                verification = (retired_package / "verification.md").read_text(encoding="utf-8")
                verification = re.sub(r"\| PASS \|", "| pending |", verification)
                verification = re.sub(
                    r"(?m)^(- (?:Dependency graph|Public API and visibility|Module-level tests|Consumer integration and build|App-shell allowlist):) PASS$",
                    r"\1 pending",
                    verification,
                )
                (retired_package / "verification.md").write_text(verification, encoding="utf-8")
                meta_path = retired_package / "meta.json"
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta.update(
                    status="implementing", verification_status="pending",
                    verified_at=None, verification_state=None, problems=[],
                )
                meta_path.write_text(json.dumps(meta), encoding="utf-8")
            normal_status, normal_errors = archive_implementation(
                retire_repo, "ios", "sample", "sample", False
            )
            assert normal_status == "BLOCKED" and any("requires verified status" in error for error in normal_errors)
            retire_dry_run, retire_errors = archive_implementation(
                retire_repo, "ios", "sample", "sample", False, retire="superseded"
            )
            assert retire_dry_run == "DRY-RUN", retire_errors
            ios_prior = retire_repo / "iOS/specs/sample/SPECIFICATION.md"
            ios_prior.write_bytes(b"previous delivered iOS baseline\n")
            retirement_before = tree_signature(retire_repo)
            rollback_status, _ = archive_implementation(
                retire_repo, "ios", "sample", "sample", True, retire="superseded", _fault="receipt"
            )
            assert rollback_status == "BLOCKED" and tree_signature(retire_repo) == retirement_before
            retire_status, retire_errors = archive_implementation(
                retire_repo, "ios", "sample", "sample", True, retire="superseded"
            )
            assert retire_status == "APPLIED", retire_errors
            assert ios_prior.read_bytes() == b"previous delivered iOS baseline\n"
            ios_retired_receipt = retire_repo / f"iOS/specs/sample/archive/{date.today().isoformat()}-sample/archive-receipt.json"
            assert validate_implementation_retirement_receipt(retire_repo, ios_retired_receipt, "sample", "ios") == []
            assert validate_implementation_receipt(retire_repo, ios_retired_receipt, "sample", "ios")
            assert validate_archived_disposition(
                retire_repo, "sample", "ios", ios_retired_receipt.relative_to(retire_repo).as_posix()
            )
            android_prior = retire_repo / "Android/specs/sample/SPECIFICATION.md"
            android_prior.write_bytes(b"previous delivered Android baseline\n")
            android_status, android_errors = archive_implementation(
                retire_repo, "android", "sample", "sample", True, retire="cancelled"
            )
            assert android_status == "APPLIED", android_errors
            assert android_prior.read_bytes() == b"previous delivered Android baseline\n"
            android_retired_receipt = retire_repo / f"Android/specs/sample/archive/{date.today().isoformat()}-sample/archive-receipt.json"
            assert validate_implementation_retirement_receipt(retire_repo, android_retired_receipt, "sample", "android") == []
            assert active_product_references(retire_repo, "sample") == []
        status, errors = archive_implementation(repo, "ios", "sample", "sample", False)
        assert status == "DRY-RUN", errors
        escape = repo / "escape"; escape.mkdir(); (escape / "marker.txt").write_text("outside archive namespace\n")
        escape_before = tree_signature(escape)
        outside_contract = escape / "mutable-contract.md"
        outside_contract.write_bytes((package / "design.md").read_bytes())
        nested_link = package / "evidence/external-contract.md"
        nested_link.symlink_to(outside_contract)
        unsafe_before = tree_signature(repo); outside_before = outside_contract.read_bytes()
        status, errors = archive_implementation(repo, "ios", "sample", "sample", True)
        assert status == "BLOCKED" and any("unsafe file entry" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and outside_contract.read_bytes() == outside_before
        nested_link.unlink()
        escape_before = tree_signature(escape)
        ios_archive_namespace = repo / "iOS/specs/sample/archive"
        ios_archive_namespace.symlink_to(escape, target_is_directory=True)
        unsafe_before = tree_signature(repo)
        status, errors = archive_implementation(repo, "ios", "sample", "sample", True)
        assert status == "BLOCKED" and any("symlink ancestor" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and tree_signature(escape) == escape_before
        ios_archive_namespace.unlink(); ios_archive_namespace.mkdir()
        dangling_target = ios_archive_namespace / f"{date.today().isoformat()}-sample"
        dangling_target.symlink_to(repo / "missing-implementation-target", target_is_directory=True)
        unsafe_before = tree_signature(repo)
        status, errors = archive_implementation(repo, "ios", "sample", "sample", True)
        assert status == "BLOCKED" and any("archive collision" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and tree_signature(escape) == escape_before
        dangling_target.unlink()
        ios_durable = repo / "iOS/specs/sample/SPECIFICATION.md"
        ios_durable.symlink_to(repo / "iOS/specs/sample/changes/sample/implementation-spec.md")
        status, errors = archive_implementation(repo, "ios", "sample", "sample", False)
        assert status == "BLOCKED" and any("non-symlink" in error for error in errors)
        ios_durable.unlink()
        ios_durable.write_bytes(b"prior platform baseline\n")
        before_implementation = tree_signature(repo)
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="pre-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="post-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="state-check")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="receipt")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True, _fault="baseline-write")
        assert status == "BLOCKED" and tree_signature(repo) == before_implementation
        status, _ = archive_implementation(repo, "ios", "sample", "sample", True); assert status == "APPLIED"
        assert (package / "ARCHIVED.md").is_file()
        assert ios_durable.read_bytes() != b"prior platform baseline\n"
        ios_durable_text = ios_durable.read_text(encoding="utf-8")
        assert "specs/product/sample/SPECIFICATION.md" in ios_durable_text
        assert "archive product completed" in ios_durable_text
        product_baseline_line = next(
            line for line in ios_durable_text.splitlines() if "Продуктовый baseline" in line
        )
        assert artifact_language.authored_text_is_russian(product_baseline_line)
        technical_payload = durable_specification_payload(
            kind="implementation", feature="technical-sample", platform="iOS",
            source_path="iOS/specs/technical-sample/archive/2026-07-16-sample/implementation-spec.md",
            source_payload=b"# Technical contract\n", archive_path="iOS/specs/technical-sample/archive/2026-07-16-sample",
            evidence_path="iOS/specs/technical-sample/archive/2026-07-16-sample/archive-receipt.json",
        ).decode("utf-8")
        assert "Продуктовый baseline" not in technical_payload and "specs/product/" not in technical_payload
        ios_receipt = repo / f"iOS/specs/sample/archive/{date.today().isoformat()}-sample/archive-receipt.json"
        historical_errors = validate_implementation_receipt(repo, ios_receipt, "sample", "ios")
        assert historical_errors == [], historical_errors
        ios_archive_root = ios_receipt.parent
        original_receipt = ios_receipt.read_bytes()
        nested_receipt_name = ios_archive_root / "evidence/archive-receipt.json"
        nested_receipt_name.write_bytes(b"nested receipt-named evidence")
        assert any("integrity mismatch" in item for item in validate_implementation_receipt(repo, ios_receipt, "sample", "ios"))
        nested_receipt_name.unlink()
        assert validate_implementation_receipt(repo, ios_receipt, "sample", "ios") == []
        ds_store = ios_archive_root / ".DS_Store"
        ds_store.write_bytes(b"v2 ignored metadata")
        assert validate_implementation_receipt(repo, ios_receipt, "sample", "ios") == []
        ds_store.write_bytes(b"v2 changed ignored metadata")
        assert validate_implementation_receipt(repo, ios_receipt, "sample", "ios") == []
        ds_store.unlink()
        v1_receipt = json.loads(original_receipt)
        v1_receipt["schema_version"] = 1; v1_receipt.pop("durable_specification")
        ios_receipt.write_text(json.dumps(v1_receipt), encoding="utf-8")
        ds_store.write_bytes(b"later stray metadata")
        assert validate_implementation_receipt(repo, ios_receipt, "sample", "ios") == []
        ds_store.unlink()
        ds_store.write_bytes(b"listed metadata")
        listed_files, listed_digest = archive_integrity(ios_archive_root, ignore_ds_store=False)
        v1_receipt["integrity"] = {"algorithm": "sha256", "files": listed_files, "digest": listed_digest}
        ios_receipt.write_text(json.dumps(v1_receipt), encoding="utf-8")
        assert validate_implementation_receipt(repo, ios_receipt, "sample", "ios") == []
        ds_store.write_bytes(b"mutated listed metadata")
        assert any("integrity mismatch" in item for item in validate_implementation_receipt(repo, ios_receipt, "sample", "ios"))
        ds_store.unlink(); ios_receipt.write_bytes(original_receipt)
        outside_receipt = escape / "mutable-receipt.json"; outside_receipt.write_bytes(original_receipt)
        ios_receipt.unlink(); ios_receipt.symlink_to(outside_receipt)
        assert any("unsafe file entry" in item for item in validate_implementation_receipt(repo, ios_receipt, "sample", "ios"))
        ios_receipt.unlink(); ios_receipt.write_bytes(original_receipt)
        meta_path = ios_archive_root / "meta.json"; original_meta_bytes = meta_path.read_bytes()
        outside_meta = escape / "mutable-meta.json"; outside_meta.write_bytes(original_meta_bytes)
        meta_path.unlink(); meta_path.symlink_to(outside_meta)
        assert any("unsafe file entry" in item for item in validate_implementation_receipt(repo, ios_receipt, "sample", "ios"))
        meta_path.unlink(); meta_path.write_bytes(original_meta_bytes)
        state_path = ios_archive_root / "evidence/verification-state.json"; original_state_bytes = state_path.read_bytes()
        outside_state = escape / "mutable-state.json"; outside_state.write_bytes(original_state_bytes)
        state_path.unlink(); state_path.symlink_to(outside_state)
        assert any("unsafe file entry" in item for item in validate_implementation_receipt(repo, ios_receipt, "sample", "ios"))
        state_path.unlink(); state_path.write_bytes(original_state_bytes)
        ios_namespace = ios_archive_root.parent; moved_namespace = escape / "ios-archive-storage"
        shutil.move(str(ios_namespace), str(moved_namespace)); ios_namespace.symlink_to(moved_namespace, target_is_directory=True)
        symlinked_receipt = ios_namespace / ios_archive_root.name / "archive-receipt.json"
        assert any("symlink ancestor" in item for item in validate_implementation_receipt(repo, symlinked_receipt, "sample", "ios"))
        assert validate_archived_disposition(repo, "sample", "ios", symlinked_receipt.relative_to(repo).as_posix())
        ios_namespace.unlink(); shutil.move(str(moved_namespace), str(ios_namespace))
        ios_receipt = ios_namespace / ios_archive_root.name / "archive-receipt.json"
        current_payload = ios_durable.read_bytes()
        ios_durable.write_bytes(b"newer platform baseline\n")
        assert validate_implementation_receipt(repo, ios_receipt, "sample", "ios") == []
        ios_durable.write_bytes(current_payload)
        escape_before = tree_signature(escape)
        android_archive_namespace = repo / "Android/specs/sample/archive"
        android_archive_namespace.symlink_to(escape, target_is_directory=True)
        unsafe_before = tree_signature(repo)
        status, errors = archive_implementation(repo, "android", "sample", "sample", True)
        assert status == "BLOCKED" and any("symlink ancestor" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and tree_signature(escape) == escape_before
        android_archive_namespace.unlink()
        android_nested_receipt = android_package / "evidence/archive-receipt.json"
        android_nested_receipt.write_bytes(b"integrity-bound nested receipt-named evidence")
        platform_validator = load_validator(); android_adapter = platform_validator.load_adapter(repo, "android")
        android_meta = json.loads((android_package / "meta.json").read_text(encoding="utf-8"))
        android_state = platform_validator.compute_state(repo, android_adapter, android_package, android_meta)
        android_state["captured_at"] = "2026-07-15T12:00:00Z"
        (android_package / "evidence/verification-state.json").write_text(json.dumps(android_state), encoding="utf-8")
        status, errors = archive_implementation(repo, "android", "sample", "sample", True)
        assert status == "APPLIED", errors
        assert (android_package / "ARCHIVED.md").is_file()
        assert (repo / "Android/specs/sample/SPECIFICATION.md").is_file()
        android_receipt = repo / f"Android/specs/sample/archive/{date.today().isoformat()}-sample/archive-receipt.json"
        archived_android_nested = android_receipt.parent / "evidence/archive-receipt.json"
        original_nested_payload = archived_android_nested.read_bytes()
        assert validate_implementation_receipt(repo, android_receipt, "sample", "android") == []
        archived_android_nested.write_bytes(b"mutated nested receipt-named evidence")
        assert any("integrity mismatch" in item for item in validate_implementation_receipt(repo, android_receipt, "sample", "android"))
        archived_android_nested.write_bytes(original_nested_payload)
        assert validate_implementation_receipt(repo, android_receipt, "sample", "android") == []
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
        load_validator().load_product_validator().write_fixture_receipt(repo, "sample")
        reserved = product.parent / "retirement-request.json"
        reserved.write_text("reserved collision\n", encoding="utf-8")
        collision_status, collision_errors = archive_product(repo, "sample", request, False)
        assert collision_status == "BLOCKED" and any("reserved retirement-request.json" in error for error in collision_errors)
        reserved.unlink()
        status, _ = archive_product(repo, "sample", request, False); assert status == "DRY-RUN"
        default_status, default_errors = archive_product(repo, "sample", None, False)
        assert default_status == "DRY-RUN", default_errors
        request_payload_before = request.read_bytes()
        outside_request = escape / "mutable-retirement-request.json"; outside_request.write_bytes(request_payload_before)
        request.unlink(); request.symlink_to(outside_request)
        unsafe_before = tree_signature(repo); outside_before = outside_request.read_bytes()
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "BLOCKED" and any("archive request" in error and "unsafe" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and outside_request.read_bytes() == outside_before
        request.unlink(); request.write_bytes(request_payload_before)
        request_parent = request.parent; moved_request_parent = escape / "retirement-request-parent"
        shutil.move(str(request_parent), str(moved_request_parent))
        request_parent.symlink_to(moved_request_parent, target_is_directory=True)
        unsafe_before = tree_signature(repo)
        status, errors = archive_product(repo, "sample", None, True)
        assert status == "BLOCKED" and any("symlink ancestor" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and outside_request.read_bytes() == outside_before
        request_parent.unlink(); shutil.move(str(moved_request_parent), str(request_parent))
        request = request_parent / request.name
        nested_product = product.parent / "nested"; nested_product.mkdir()
        product_link = nested_product / "mutable-candidate.md"; product_link.symlink_to(outside_contract)
        unsafe_before = tree_signature(repo); outside_before = outside_contract.read_bytes()
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "BLOCKED" and any("unsafe file entry" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and outside_contract.read_bytes() == outside_before
        product_link.unlink(); nested_product.rmdir()
        special = product.parent / "candidate.pipe"; os.mkfifo(special)
        unsafe_before = tree_signature(repo)
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "BLOCKED" and any("unsafe file entry" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and outside_contract.read_bytes() == outside_before
        special.unlink()
        escape_before = tree_signature(escape)
        product_archive_namespace = repo / "specs/product/_archive"
        product_archive_namespace.symlink_to(escape, target_is_directory=True)
        unsafe_before = tree_signature(repo)
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "BLOCKED" and any("symlink ancestor" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and tree_signature(escape) == escape_before
        product_archive_namespace.unlink()
        product_archive_parent = product_archive_namespace / "sample"
        product_archive_parent.mkdir(parents=True)
        product_dangling_target = product_archive_parent / f"{date.today().isoformat()}-sample"
        product_dangling_target.symlink_to(repo / "missing-product-target", target_is_directory=True)
        unsafe_before = tree_signature(repo)
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "BLOCKED" and any("product archive collision" in error for error in errors)
        assert tree_signature(repo) == unsafe_before and tree_signature(escape) == escape_before
        product_dangling_target.unlink()
        product_durable = repo / "specs/product/sample/SPECIFICATION.md"
        product_durable.symlink_to(repo / "specs/product/sample/spec.md")
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("non-symlink" in error for error in errors)
        product_durable.unlink()
        product_durable.write_bytes(b"prior product baseline\n")
        before_product = tree_signature(repo)
        status, _ = archive_product(repo, "sample", request, True, _fault="pre-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, _ = archive_product(repo, "sample", request, True, _fault="post-move")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, _ = archive_product(repo, "sample", request, True, _fault="post-copy")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, _ = archive_product(repo, "sample", request, True, _fault="tombstone-write")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, _ = archive_product(repo, "sample", request, True, _fault="baseline-write")
        assert status == "BLOCKED" and tree_signature(repo) == before_product
        status, errors = archive_product(repo, "sample", request, True); assert status == "APPLIED", errors
        product_archive = repo / f"specs/product/_archive/sample/{date.today().isoformat()}-sample"
        assert (product_archive / "retirement-request.json").read_bytes() == request.read_bytes()
        assert (repo / "specs/product/sample/spec.md").is_file()
        assert "ARCHIVED" in (repo / "specs/product/sample/spec.md").read_text()
        assert product_durable.is_file() and product_durable.read_bytes() != b"prior product baseline\n"
        status, errors = archive_product(repo, "sample", request, False)
        assert status == "BLOCKED" and any("collision" in error for error in errors)
        status, _ = archive_product(repo, "../escape", None, False); assert status == "BLOCKED"
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); terminal_fixture(repo); terminal_android_fixture(repo)
        request = repo / "specs/product/_retirement-requests/sample" / f"{date.today().isoformat()}-sample.json"
        request.parent.mkdir(parents=True)
        request.write_text(json.dumps({
            "feature": "sample", "reason": "cancelled",
            "retirement_approval": {"approved_by": "Product owner", "evidence": "явное решение об отмене незавершённого изменения"},
            "platforms": {
                "ios": {"disposition": "cancelled", "evidence": "реализация явно отменена владельцем продукта"},
                "android": {"disposition": "cancelled", "evidence": "реализация явно отменена владельцем продукта"},
            },
        }, ensure_ascii=False), encoding="utf-8")
        shutil.rmtree(repo / "iOS/specs/sample/changes/sample")
        shutil.rmtree(repo / "Android/specs/sample/changes/sample")
        baseline = repo / "specs/product/sample/SPECIFICATION.md"
        baseline.write_bytes(b"previous delivered baseline\n")
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "APPLIED", errors
        assert baseline.read_bytes() == b"previous delivered baseline\n"
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); terminal_fixture(repo); terminal_android_fixture(repo)
        request = repo / "specs/product/_retirement-requests/sample" / f"{date.today().isoformat()}-sample.json"
        request.parent.mkdir(parents=True)
        request.write_text(json.dumps({
            "feature": "sample", "reason": "superseded",
            "retirement_approval": {"approved_by": "Product owner", "evidence": "явное решение заменить незавершённый вариант"},
            "platforms": {
                "ios": {"disposition": "cancelled", "evidence": "реализация не начиналась и явно закрыта"},
                "android": {"disposition": "cancelled", "evidence": "реализация не начиналась и явно закрыта"},
            },
        }, ensure_ascii=False), encoding="utf-8")
        shutil.rmtree(repo / "iOS/specs/sample/changes/sample")
        shutil.rmtree(repo / "Android/specs/sample/changes/sample")
        status, errors = archive_product(repo, "sample", request, True)
        assert status == "APPLIED", errors
        assert not (repo / "specs/product/sample/SPECIFICATION.md").exists()
    print("archive-change self-test: PASS (implementation/product gates, isolation, collision safety)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("implementation", "product"))
    parser.add_argument("--platform"); parser.add_argument("--feature"); parser.add_argument("--change")
    parser.add_argument("--retire", choices=("superseded", "cancelled"))
    parser.add_argument("--request", type=Path); parser.add_argument("--apply", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]); parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test: return self_test()
    if not args.mode or not args.feature: parser.error("mode and --feature are required")
    if args.mode == "implementation":
        if not args.platform: parser.error("implementation mode requires --platform")
        status, details = archive_implementation(args.root, args.platform, args.feature, args.change, args.apply, args.retire)
    else:
        if args.retire: parser.error("--retire applies only to implementation mode")
        status, details = archive_product(args.root, args.feature, args.request, args.apply)
    print(f"Archive {args.mode}: {status}")
    for detail in details: print(f"- {detail}")
    return 0 if status in {"DRY-RUN", "APPLIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
