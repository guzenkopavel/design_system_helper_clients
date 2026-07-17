#!/usr/bin/env python3
"""Staged-index pre-commit gate. Never stages, commits, pushes, or prints secrets."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

from platform_rule_profiles import RuleProfileError, validate_pre_commit_profile
import git_change_paths as change_paths
import platform_path_ownership as path_ownership


FAIL = "FAIL"
UNKNOWN = "UNKNOWN"
PASS = "PASS"
NA = "N/A"
ACTIVE_STATUSES = {"planned", "implementing", "verified"}
EXPECTED_PLATFORM_ROOTS = ("iOS", "Android")
HARNESS_PREFIXES = (
    "workflow/", "process/", ".agents/", ".codex/", ".claude/",
    ".cursor/", ".opencode/", ".githooks/", "AGENTS.md",
    "iOS/AGENTS.md", "Android/AGENTS.md", "iOS/workflow/", "Android/workflow/",
)
COMMON_GENERATED = (
    "**/.DS_Store", "**/*.xcuserstate", "**/DerivedData/**", "**/.gradle/**",
    "**/.idea/**", "**/build/**", "**/*.log", "**/*.tmp", "**/*.swp",
)
COMMON_SECRET_PATHS = (
    "**/.env", "**/.env.*", "**/local.properties", "**/*.p8", "**/*.p12",
    "**/*.mobileprovision", "**/*.keystore", "**/*.jks", "**/*.pem", "**/*.key",
)
DEBUG_PATTERNS = (
    re.compile(rb"\bTEMP_DEBUG\b|\bINVESTIGATION_ONLY\b|\bDO_NOT_COMMIT\b", re.I),
    re.compile(rb"\bdebugPrint\s*\("),
    re.compile(rb"\b(?:Log\.d|println)\s*\(\s*[\"']DEBUG", re.I),
)
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(
        rb"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*[\"'][^\"'\r\n]{12,}[\"']"
    ),
)
PLACEHOLDER_RE = re.compile(rb"\b(?:TODO|TBD|FIXME)\b|<[^>\r\n]+>|\{\{|\}\}", re.I)
CONFLICT_RE = re.compile(rb"(?m)^(?:<<<<<<< |=======\s*$|>>>>>>> )")
RECEIPT_SCHEMA_VERSION = 1
RECEIPT_TTL_SECONDS = 300
RECEIPT_DIRECTORY_MODE = 0o700
RECEIPT_FILE_MODE = 0o600
RECONCILE_RECEIPT_SCHEMA_VERSION = 1
RECONCILE_RECEIPT_TTL_SECONDS = 300


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=repo, input=input_bytes, capture_output=True, check=False
    )


def repository_root(start: Path | None = None) -> Path:
    result = git((start or Path.cwd()).resolve(), "rev-parse", "--show-toplevel")
    if result.returncode:
        raise ValueError("not inside a Git repository")
    return Path(result.stdout.decode().strip()).resolve()


def staged_entries(repo: Path) -> list[change_paths.ChangeEntry]:
    return change_paths.staged_entries(repo)


def staged_fingerprint(repo: Path) -> str:
    names = git(repo, "diff", "--cached", "--name-status", "-z", "--find-renames").stdout
    index = git(repo, "ls-files", "-s", "-z").stdout
    diff = git(repo, "diff", "--cached", "--binary", "--no-ext-diff").stdout
    return hashlib.sha256(names + b"\0INDEX\0" + index + b"\0DIFF\0" + diff).hexdigest()


class ReceiptError(ValueError):
    pass


def reject_non_finite_json(value: str):
    raise ReceiptError(f"pre-commit receipt contains non-finite JSON constant: {value}")


def git_directory(repo: Path) -> str:
    result = git(repo, "rev-parse", "--absolute-git-dir")
    if result.returncode:
        raise ReceiptError("repository Git directory is unavailable")
    return str(Path(result.stdout.decode().strip()).resolve())


def receipt_directory(*, create: bool) -> Path:
    root = Path(tempfile.gettempdir()) / f"mobile-harness-precommit-{os.getuid()}"
    if create:
        try:
            root.mkdir(mode=RECEIPT_DIRECTORY_MODE)
        except FileExistsError:
            pass
    try:
        metadata = root.lstat()
    except FileNotFoundError as error:
        raise ReceiptError("pre-commit receipt is absent") from error
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != RECEIPT_DIRECTORY_MODE
        or metadata.st_uid != os.getuid()
    ):
        raise ReceiptError("pre-commit receipt directory is not private mode 0700")
    return root


def receipt_path(repo: Path, *, create_directory: bool = False) -> Path:
    root = receipt_directory(create=create_directory)
    identity = hashlib.sha256(
        (str(repo.resolve()) + "\0" + git_directory(repo)).encode("utf-8")
    ).hexdigest()
    return root / f"{identity}.json"


def reconcile_receipt_directory(*, create: bool) -> Path:
    root = Path(tempfile.gettempdir()) / f"mobile-harness-reconcile-precommit-{os.getuid()}"
    if create:
        try:
            root.mkdir(mode=RECEIPT_DIRECTORY_MODE)
        except FileExistsError:
            pass
    try:
        metadata = root.lstat()
    except FileNotFoundError as error:
        raise ReceiptError("reconcile receipt is absent") from error
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != RECEIPT_DIRECTORY_MODE
        or metadata.st_uid != os.getuid()
    ):
        raise ReceiptError("reconcile receipt directory is not private mode 0700")
    return root


def reconcile_receipt_path(repo: Path) -> Path:
    root = reconcile_receipt_directory(create=False)
    identity = hashlib.sha256(
        (str(repo.resolve()) + "\0" + git_directory(repo)).encode("utf-8")
    ).hexdigest()
    return root / f"{identity}.json"


def read_reconcile_receipt(repo: Path) -> dict[str, object] | None:
    try:
        target = reconcile_receipt_path(repo)
        metadata = target.lstat()
    except (FileNotFoundError, ReceiptError):
        return None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != RECEIPT_FILE_MODE
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
    ):
        return None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(target, flags)
        with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
            payload = json.load(stream, parse_constant=reject_non_finite_json)
    except (OSError, json.JSONDecodeError, ReceiptError):
        return None
    return payload if isinstance(payload, dict) else None


def staged_content_hash(repo: Path, raw: str) -> str | None:
    blob, _mode = staged_blob(repo, raw)
    if blob is None:
        return None
    return hashlib.sha256(blob).hexdigest()


def valid_reconcile_receipt_for_staged_set(
    repo: Path, payload: dict[str, object] | None, staged_paths: set[str]
) -> dict[str, object] | None:
    if not payload:
        return None
    expected = {
        "schema_version", "repo", "git_dir", "platform_root", "platform", "feature",
        "change", "package", "outcome", "coverage_mode", "intended_paths",
        "mutable_paths", "content_hashes", "created_at", "expires_at",
    }
    if set(payload) != expected or payload.get("schema_version") != RECONCILE_RECEIPT_SCHEMA_VERSION:
        return None
    if payload.get("repo") != str(repo.resolve()) or payload.get("git_dir") != git_directory(repo):
        return None
    if payload.get("outcome") != "ALIGNED" or payload.get("coverage_mode") != "verified-archive-package":
        return None
    intended = payload.get("intended_paths")
    mutable = payload.get("mutable_paths")
    hashes = payload.get("content_hashes")
    if (
        not isinstance(intended, list)
        or not intended
        or any(not isinstance(item, str) for item in intended)
        or sorted(set(intended)) != intended
        or set(intended) != staged_paths
        or not isinstance(mutable, list)
        or any(not isinstance(item, str) for item in mutable)
        or not set(mutable) <= staged_paths
        or not isinstance(hashes, dict)
    ):
        return None
    created = payload.get("created_at")
    expires = payload.get("expires_at")
    now = time.time()
    if (
        isinstance(created, bool)
        or isinstance(expires, bool)
        or not isinstance(created, (int, float))
        or not isinstance(expires, (int, float))
        or not math.isfinite(created)
        or not math.isfinite(expires)
        or created > now + 5
        or expires <= created
        or expires - created > RECONCILE_RECEIPT_TTL_SECONDS
        or now > expires
    ):
        return None
    for raw in mutable:
        expected_hash = hashes.get(raw)
        if expected_hash is not None and not isinstance(expected_hash, str):
            return None
        if staged_content_hash(repo, raw) != expected_hash:
            return None
    return payload


def reconcile_receipt_trail(
    receipt: dict[str, object] | None, adapter: dict[str, object], candidate: str
) -> dict[str, object] | None:
    if not receipt:
        return None
    if receipt.get("platform_root") != str(adapter.get("platform_root")):
        return None
    mutable = receipt.get("mutable_paths")
    if not isinstance(mutable, list) or candidate not in mutable:
        return None
    package = receipt.get("package")
    if not isinstance(package, str) or not package:
        return None
    return {
        "package": package,
        "task": "reconcile-receipt",
        "done": True,
        "evidence": True,
        "scopes": [],
        "command": "reconcile-implementation inspect",
        "source": "archived-package",
        "current": True,
    }


def staged_path_set(repo: Path, intended: list[str] | None = None) -> tuple[list[str], list[str]]:
    entries = staged_entries(repo)
    if intended is not None:
        entries, errors = change_paths.normalize_for_intent(repo, entries, intended, staged=True)
    else:
        errors = []
    return change_paths.path_sets(entries)["identity_paths"], errors


def issue_receipt(repo: Path, intended_paths: list[str], fingerprint: str) -> None:
    target = receipt_path(repo, create_directory=True)
    now = time.time()
    payload = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "repo": str(repo.resolve()),
        "git_dir": git_directory(repo),
        "fingerprint": fingerprint,
        "intended_paths": sorted(intended_paths),
        "created_at": now,
        "expires_at": now + RECEIPT_TTL_SECONDS,
    }
    temporary = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, RECEIPT_FILE_MODE)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        os.chmod(target, RECEIPT_FILE_MODE, follow_symlinks=False)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def read_receipt(repo: Path, *, consume: bool) -> dict[str, object]:
    target = receipt_path(repo)
    try:
        metadata = target.lstat()
    except FileNotFoundError as error:
        raise ReceiptError("pre-commit receipt is absent") from error
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != RECEIPT_FILE_MODE
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
    ):
        raise ReceiptError("pre-commit receipt must be a private regular mode 0600 file")
    source = target
    if consume:
        source = target.parent / f".{target.name}.{uuid.uuid4().hex}.consuming"
        try:
            os.replace(target, source)
        except FileNotFoundError as error:
            raise ReceiptError("pre-commit receipt was already consumed") from error
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(source, flags)
        with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != RECEIPT_FILE_MODE:
                raise ReceiptError("pre-commit receipt mode changed during validation")
            try:
                payload = json.load(stream, parse_constant=reject_non_finite_json)
            except json.JSONDecodeError as error:
                raise ReceiptError("pre-commit receipt JSON is malformed") from error
    finally:
        if consume:
            try:
                source.unlink()
            except FileNotFoundError:
                pass
    if not isinstance(payload, dict):
        raise ReceiptError("pre-commit receipt payload is malformed")
    return payload


def validate_receipt(repo: Path, payload: dict[str, object]) -> str:
    expected_keys = {
        "schema_version", "repo", "git_dir", "fingerprint", "intended_paths",
        "created_at", "expires_at",
    }
    if set(payload) != expected_keys or payload.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        return "pre-commit receipt schema is malformed"
    if payload.get("repo") != str(repo.resolve()) or payload.get("git_dir") != git_directory(repo):
        return "pre-commit receipt belongs to a different repository"
    intended = payload.get("intended_paths")
    if (
        not isinstance(intended, list)
        or not intended
        or any(not isinstance(item, str) for item in intended)
        or intended != sorted(set(intended))
        or intended != staged_path_set(repo, intended)[0]
    ):
        return "pre-commit receipt intended paths do not match the staged index"
    identity_errors = staged_path_set(repo, intended)[1]
    if identity_errors:
        return "pre-commit receipt change identity is invalid: " + "; ".join(identity_errors)
    created = payload.get("created_at")
    expires = payload.get("expires_at")
    now = time.time()
    if (
        isinstance(created, bool)
        or isinstance(expires, bool)
        or not isinstance(created, (int, float))
        or not isinstance(expires, (int, float))
        or not math.isfinite(created)
        or not math.isfinite(expires)
        or created > now + 5
        or expires <= created
        or expires - created > RECEIPT_TTL_SECONDS
        or now > expires
    ):
        return "pre-commit receipt is stale or has an invalid lifetime"
    if payload.get("fingerprint") != staged_fingerprint(repo):
        return "pre-commit receipt staged fingerprint is stale"
    return ""


def hook_evaluate(repo: Path, *, consume: bool) -> dict[str, object]:
    checks: list[dict[str, str]] = []
    intended: list[str] = []
    try:
        payload = read_receipt(repo, consume=consume)
        detail = validate_receipt(repo, payload)
        if detail:
            add(checks, "receipt.authorization", FAIL, detail)
        else:
            intended = [str(item) for item in payload["intended_paths"]]
            action = "consumed" if consume else "validated without consumption"
            add(checks, "receipt.authorization", PASS, f"fresh exact receipt {action}")
    except (OSError, ReceiptError, ValueError) as error:
        add(checks, "receipt.authorization", FAIL, str(error))
    if any(item["status"] == FAIL for item in checks):
        return {"status": FAIL, "fingerprint": staged_fingerprint(repo), "checks": checks}
    integrity = evaluate(repo, intended, require_intended=True)
    combined = checks + list(integrity["checks"])
    statuses = {item["status"] for item in combined}
    status = FAIL if FAIL in statuses else UNKNOWN if UNKNOWN in statuses else PASS
    return {"status": status, "fingerprint": integrity["fingerprint"], "checks": combined}


def canonical_evaluate(repo: Path, intended_paths: list[str]) -> dict[str, object]:
    report = evaluate(repo, intended_paths, require_intended=True)
    if report["status"] != PASS:
        return report
    try:
        intended, _errors = safe_intended_paths(intended_paths)
        issue_receipt(repo, intended, str(report["fingerprint"]))
        add(report["checks"], "receipt.created", PASS, "fresh private exact receipt created")
    except (OSError, ReceiptError, ValueError) as error:
        add(report["checks"], "receipt.created", FAIL, str(error))
        report["status"] = FAIL
    return report


def staged_blob(repo: Path, path: str) -> tuple[bytes | None, str | None]:
    info = git(repo, "ls-files", "-s", "--", path).stdout.decode("utf-8", errors="replace").strip()
    if not info:
        return None, None
    mode = info.split(maxsplit=1)[0]
    blob = git(repo, "show", f":{path}")
    return (blob.stdout if blob.returncode == 0 else None), mode


def glob_match(path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    normalized = PurePosixPath(path).as_posix()
    for pattern in patterns:
        variants = (
            pattern,
            pattern.replace("/**/", "/"),
            pattern.removeprefix("**/"),
        )
        if any(fnmatch.fnmatchcase(normalized, value) for value in variants):
            return True
    return False


def path_under(path: str, roots: list[str]) -> bool:
    value = PurePosixPath(path)
    return any(value == PurePosixPath(root) or PurePosixPath(root) in value.parents for root in roots)


def load_adapter_state(
    repo: Path, *, from_index: bool = False
) -> tuple[list[dict[str, object]], dict[str, str]]:
    adapters: list[dict[str, object]] = []
    errors: dict[str, str] = {}
    for platform_root in EXPECTED_PLATFORM_ROOTS:
        relative_path = f"{platform_root}/workflow/platform-contract.json"
        path = repo / relative_path
        try:
            raw = index_text(repo, relative_path) if from_index else path.read_text(encoding="utf-8")
            if raw is None:
                raise OSError("platform contract is missing from staged index")
            data = json.loads(raw)
            validate_pre_commit_profile(data)
            if data.get("platform_root") != platform_root:
                raise RuleProfileError("platform_root does not match contract location")
        except (OSError, json.JSONDecodeError, RuleProfileError) as error:
            errors[platform_root] = str(error)
            continue
        adapters.append(data)
    return adapters, errors


def load_adapters(repo: Path, *, from_index: bool = False) -> list[dict[str, object]]:
    return load_adapter_state(repo, from_index=from_index)[0]


def adapter_for_production(path: str, adapters: list[dict[str, object]]) -> dict[str, object] | None:
    for adapter in adapters:
        roots = [str(item) for item in adapter["production_roots"]]
        excluded = [str(item) for item in adapter["protected_roots"] + adapter["production_exclusions"]]
        if path_under(path, roots) and not path_under(path, excluded):
            return adapter
    return None


def index_paths(repo: Path) -> list[str]:
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in git(repo, "ls-files", "-z").stdout.split(b"\0") if item
    ]


def index_text(repo: Path, path: str) -> str | None:
    blob, mode = staged_blob(repo, path)
    if blob is None or mode == "120000":
        return None
    return blob.decode("utf-8", errors="replace")


def parse_task_paths(body: str) -> list[str]:
    match = re.search(r"(?mi)^-\s*Paths:\s*(.+)$", body)
    if not match:
        return []
    return [
        item.group(2).strip()
        for item in re.finditer(r"(?:^|;\s*)(existing|proposed):\s*([^;]+)", match.group(1))
    ]


def parse_task_scopes(body: str) -> list[str]:
    match = re.search(r"(?mi)^-\s*Engineering scopes:\s*(\[[^\r\n]*\])\s*$", body)
    if not match:
        return []
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []


def parse_task_command(body: str) -> str | None:
    match = re.search(r"(?mi)^-\s*Discovered command:\s*(\S.*)$", body)
    if not match or match.group(1).strip().casefold() in {"none", "n/a"}:
        return None
    return match.group(1).strip()


def declared_covers(repo: Path, declared: str, candidate: str) -> bool:
    raw = PurePosixPath(declared.rstrip("/")); value = PurePosixPath(candidate)
    if raw == value:
        return True
    target = repo / raw
    directory_boundary = declared.endswith("/") or target.is_dir() or not raw.suffix
    return directory_boundary and raw in value.parents


def task_trails(
    repo: Path, adapter: dict[str, object], candidate: str, changed_paths: set[str]
) -> list[dict[str, object]]:
    package_root = str(adapter["package_root"]).rstrip("/")
    meta_re = re.compile(
        rf"^{re.escape(package_root)}/[^/]+/{re.escape(str(adapter['active_changes_namespace']))}/[^/]+/meta\.json$"
    )
    paths = index_paths(repo)
    results: list[dict[str, object]] = []
    for meta_path in paths:
        if not meta_re.fullmatch(meta_path):
            continue
        raw_meta = index_text(repo, meta_path)
        if raw_meta is None:
            continue
        try:
            meta = json.loads(raw_meta)
        except json.JSONDecodeError:
            continue
        if meta.get("status") not in ACTIVE_STATUSES:
            continue
        package = meta_path.removesuffix("/meta.json")
        for task_path in paths:
            if not re.fullmatch(rf"{re.escape(package)}/plan/task-\d{{3}}\.md", task_path):
                continue
            body = index_text(repo, task_path) or ""
            if not any(declared_covers(repo, declared, candidate) for declared in parse_task_paths(body)):
                continue
            status_match = re.search(r"(?mi)^-\s*Status:\s*(pending|done)\s*$", body)
            evidence_match = re.search(r"(?mi)^-\s*Evidence:\s*(\S+)\s*$", body)
            evidence = evidence_match.group(1) if evidence_match else "none"
            evidence_path = f"{package}/{evidence}" if evidence != "none" else ""
            evidence_blob = index_text(repo, evidence_path) if evidence_path else None
            result = {
                "package": package,
                "task": PurePosixPath(task_path).stem,
                "done": bool(status_match and status_match.group(1) == "done"),
                "evidence": bool(
                    evidence_path in changed_paths and evidence_blob and evidence_blob.strip()
                ),
                "scopes": parse_task_scopes(body),
                "command": parse_task_command(body),
            }
            results.append(result)
    return results


def archived_task_trails(
    repo: Path, adapter: dict[str, object], candidate: str, changed_paths: set[str]
) -> list[dict[str, object]]:
    package_root = str(adapter["package_root"]).rstrip("/")
    archive_namespace = str(adapter.get("archive_namespace", "archive"))
    meta_re = re.compile(
        rf"^{re.escape(package_root)}/[^/]+/{re.escape(archive_namespace)}/[^/]+/meta\.json$"
    )
    paths = index_paths(repo)
    results: list[dict[str, object]] = []
    for meta_path in paths:
        if not meta_re.fullmatch(meta_path):
            continue
        raw_meta = index_text(repo, meta_path)
        if raw_meta is None:
            continue
        try:
            meta = json.loads(raw_meta)
        except json.JSONDecodeError:
            continue
        if meta.get("status") != "archived" or meta.get("verification_status") != "PASS":
            continue
        package = meta_path.removesuffix("/meta.json")
        receipt_blob = index_text(repo, f"{package}/archive-receipt.json")
        if not receipt_blob:
            continue
        try:
            receipt = json.loads(receipt_blob)
        except json.JSONDecodeError:
            continue
        if (
            receipt.get("mode") != "implementation"
            or receipt.get("verification_status") != "PASS"
            or receipt.get("archived_path") != package
            or receipt.get("tasks_done") != receipt.get("tasks_total")
        ):
            continue
        current_archive = any(raw == package or raw.startswith(package + "/") for raw in changed_paths)
        state_ref = receipt.get("verification_state")
        state_paths: set[str] = set()
        if isinstance(state_ref, dict) and isinstance(state_ref.get("path"), str):
            state_blob = index_text(repo, f"{package}/{state_ref['path']}")
            if state_blob:
                try:
                    state = json.loads(state_blob)
                    if state.get("fingerprint") == state_ref.get("fingerprint"):
                        files = state.get("files", {})
                        if isinstance(files, dict):
                            state_paths = {
                                raw.removeprefix("repo/")
                                for raw in files
                                if isinstance(raw, str) and raw.startswith("repo/")
                            }
                except json.JSONDecodeError:
                    state_paths = set()
        covered_by_task = False
        for task_path in paths:
            if not re.fullmatch(rf"{re.escape(package)}/plan/task-\d{{3}}\.md", task_path):
                continue
            body = index_text(repo, task_path) or ""
            if not any(declared_covers(repo, declared, candidate) for declared in parse_task_paths(body)):
                continue
            covered_by_task = True
            status_match = re.search(r"(?mi)^-\s*Status:\s*(pending|done)\s*$", body)
            evidence_match = re.search(r"(?mi)^-\s*Evidence:\s*(\S+)\s*$", body)
            evidence = evidence_match.group(1) if evidence_match else "none"
            evidence_path = f"{package}/{evidence}" if evidence != "none" else ""
            evidence_blob = index_text(repo, evidence_path) if evidence_path else None
            results.append({
                "package": package,
                "task": PurePosixPath(task_path).stem,
                "done": bool(status_match and status_match.group(1) == "done"),
                "evidence": bool(evidence_blob and evidence_blob.strip()),
                "scopes": parse_task_scopes(body),
                "command": parse_task_command(body),
                "source": "archived",
                "current": current_archive,
            })
        if not covered_by_task and candidate in state_paths:
            results.append({
                "package": package,
                "task": "verification-state",
                "done": True,
                "evidence": True,
                "scopes": [],
                "command": "archive receipt verification",
                "source": "archived",
                "current": current_archive,
            })
        elif not covered_by_task and current_archive:
            results.append({
                "package": package,
                "task": "archive-receipt",
                "done": True,
                "evidence": True,
                "scopes": [],
                "command": "verified archive package receipt",
                "source": "archived-package",
                "current": current_archive,
            })
    return results


def select_package_trail(
    trails: list[dict[str, object]],
) -> tuple[dict[str, object] | None, list[str]]:
    packages = sorted(set(str(item["package"]) for item in trails))
    current_packages = sorted(set(str(item["package"]) for item in trails if item.get("current")))
    if len(current_packages) == 1:
        trails = [item for item in trails if str(item["package"]) == current_packages[0]]
        packages = current_packages
    elif len(current_packages) > 1:
        return None, current_packages
    if len(packages) > 1:
        return None, packages
    if not trails:
        return None, []
    completed = next(
        (item for item in trails if item.get("done") and item.get("evidence")), None
    )
    return completed or trails[0], packages


def worktree_task_trails(repo: Path, adapter: dict[str, object], candidate: str) -> list[dict[str, object]]:
    package_root = repo / str(adapter["package_root"])
    if not package_root.is_dir():
        return []
    results: list[dict[str, object]] = []
    for meta_path in package_root.glob(f"*/{adapter['active_changes_namespace']}/*/meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if meta.get("status") not in ACTIVE_STATUSES:
            continue
        package = meta_path.parent
        for task_path in sorted((package / "plan").glob("task-*.md")):
            body = task_path.read_text(encoding="utf-8", errors="replace")
            if any(declared_covers(repo, declared, candidate) for declared in parse_task_paths(body)):
                results.append({
                    "package": package.relative_to(repo).as_posix(),
                    "task": task_path.stem,
                    "scopes": parse_task_scopes(body),
                    "command": parse_task_command(body),
                    "source": "active",
                })
    archive_root = repo / str(adapter["package_root"])
    archive_namespace = str(adapter.get("archive_namespace", "archive"))
    for meta_path in archive_root.glob(f"*/{archive_namespace}/*/meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            receipt = json.loads((meta_path.parent / "archive-receipt.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        package = meta_path.parent
        if (
            meta.get("status") != "archived"
            or meta.get("verification_status") != "PASS"
            or receipt.get("mode") != "implementation"
            or receipt.get("verification_status") != "PASS"
            or receipt.get("archived_path") != package.relative_to(repo).as_posix()
            or receipt.get("tasks_done") != receipt.get("tasks_total")
        ):
            continue
        state_ref = receipt.get("verification_state")
        state_paths: set[str] = set()
        if isinstance(state_ref, dict) and isinstance(state_ref.get("path"), str):
            try:
                state = json.loads((package / str(state_ref["path"])).read_text(encoding="utf-8"))
                if state.get("fingerprint") == state_ref.get("fingerprint"):
                    files = state.get("files", {})
                    if isinstance(files, dict):
                        state_paths = {
                            raw.removeprefix("repo/")
                            for raw in files
                            if isinstance(raw, str) and raw.startswith("repo/")
                        }
            except (OSError, json.JSONDecodeError):
                state_paths = set()
        covered_by_task = False
        for task_path in sorted((package / "plan").glob("task-*.md")):
            body = task_path.read_text(encoding="utf-8", errors="replace")
            if any(declared_covers(repo, declared, candidate) for declared in parse_task_paths(body)):
                covered_by_task = True
                results.append({
                    "package": package.relative_to(repo).as_posix(),
                    "task": task_path.stem,
                    "scopes": parse_task_scopes(body),
                    "command": parse_task_command(body),
                    "source": "archived",
                })
        if not covered_by_task and candidate in state_paths:
            results.append({
                "package": package.relative_to(repo).as_posix(),
                "task": "verification-state",
                "scopes": [],
                "command": "archive receipt verification",
                "source": "archived",
            })
    return results


def active_spec(path: str) -> bool:
    value = PurePosixPath(path)
    if "templates" in value.parts or "_archive" in value.parts or "archive" in value.parts:
        return False
    return (
        re.fullmatch(r"specs/product/[^/_][^/]*/(?:concept|brief|ux|spec)\.md", path) is not None
        or re.match(r"^(?:iOS|Android)/specs/[^/]+/changes/[^/]+/", path) is not None
    )


def add(checks: list[dict[str, str]], check_id: str, status: str, detail: str, path: str | None = None) -> None:
    item = {"id": check_id, "status": status, "detail": detail}
    if path:
        item["path"] = path
    checks.append(item)


def run_staged_harness_lint(repo: Path) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp).resolve() / "index"
        checkout.mkdir()
        prefix = checkout.as_posix() + "/"
        exported = git(repo, "checkout-index", "--all", f"--prefix={prefix}")
        script = checkout / "workflow/scripts/harness-lint.py"
        if exported.returncode or not script.is_file():
            return FAIL, "staged harness checkout or lint script is unavailable"
        result = subprocess.run(
            ["python3", str(script), "--warn-as-error"], cwd=checkout,
            text=True, capture_output=True, check=False,
        )
        return (PASS, "staged harness lint passed") if result.returncode == 0 else (FAIL, "staged harness lint failed")


def safe_intended_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    normalized: list[str] = []
    errors: list[str] = []
    for raw in paths:
        value = PurePosixPath(raw)
        if value.is_absolute() or ".." in value.parts or value.as_posix() in {"", "."}:
            errors.append(f"unsafe intended path: {raw}")
            continue
        normalized.append(value.as_posix())
    if len(normalized) != len(set(normalized)):
        errors.append("intended paths must be unique")
    return sorted(set(normalized)), errors


def evaluate(
    repo: Path, intended_paths: list[str] | None = None, *, require_intended: bool = False,
) -> dict[str, object]:
    before = staged_fingerprint(repo)
    entries = staged_entries(repo)
    checks: list[dict[str, str]] = []
    if not entries:
        add(checks, "staged.non-empty", FAIL, "no staged changes")
        return {"status": FAIL, "fingerprint": before, "checks": checks}
    add(checks, "staged.non-empty", PASS, f"{len(entries)} staged entries")
    identity_errors: list[str] = []
    if intended_paths:
        entries, identity_errors = change_paths.normalize_for_intent(
            repo, entries, sorted(set(intended_paths)), staged=True
        )
    entry_sets = change_paths.path_sets(entries)
    staged_path_set = set(entry_sets["identity_paths"])
    intended, intended_errors = safe_intended_paths(intended_paths or [])
    if require_intended:
        if not intended_paths:
            add(checks, "staged.intended-binding", FAIL, "canonical staged gate requires explicit --path for the exact intended set")
        for detail in intended_errors:
            add(checks, "staged.intended-binding", FAIL, detail)
        for detail in identity_errors:
            add(checks, "staged.intended-binding", FAIL, detail)
        intended_set = set(intended)
        missing = sorted(intended_set - staged_path_set)
        extra = sorted(staged_path_set - intended_set)
        if missing:
            add(checks, "staged.intended-binding", FAIL, "intended paths are missing from index: " + ", ".join(missing))
        if extra:
            add(checks, "staged.intended-binding", FAIL, "index contains foreign staged paths: " + ", ".join(extra))
        if intended_paths and not intended_errors and not missing and not extra:
            add(checks, "staged.intended-binding", PASS, "staged paths exactly match the explicit intended set")

    if git(repo, "ls-files", "-u").stdout:
        add(checks, "staged.unmerged", FAIL, "unmerged index entries exist")
    else:
        add(checks, "staged.unmerged", PASS, "no unmerged index entries")
    if git(repo, "diff", "--cached", "--check").returncode:
        add(checks, "staged.diff-check", FAIL, "staged diff has whitespace/conflict errors")
    else:
        add(checks, "staged.diff-check", PASS, "staged diff check passed")

    adapters, adapter_errors = load_adapter_state(repo, from_index=True)
    changed_paths = set(entry_sets["identity_paths"])
    indexed_paths = set(index_paths(repo))
    reconcile_receipt = valid_reconcile_receipt_for_staged_set(
        repo, read_reconcile_receipt(repo), changed_paths
    )
    production_seen = False
    harness_seen = False
    trails_by_platform: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        path = entry.path
        identity_candidates = change_paths.identity_paths(entry)
        candidates = change_paths.mutable_paths(entry)
        harness_seen = harness_seen or any(
            candidate == prefix or candidate.startswith(prefix)
            for candidate in identity_candidates for prefix in HARNESS_PREFIXES
        )
        adapter = adapter_for_production(path, adapters)
        profile = adapter["pre_commit"] if adapter else None
        generated = list(COMMON_GENERATED) + (list(profile["generated_globs"]) if profile else [])
        secrets = list(COMMON_SECRET_PATHS) + (list(profile["secret_globs"]) if profile else [])
        if entry.status != "D" and glob_match(path, generated):
            add(checks, "path.generated-local", FAIL, "generated/local artifact is staged", path)
        if entry.status != "D" and glob_match(path, secrets):
            add(checks, "path.secret-material", FAIL, "secret/key material path is staged", path)

        for source in change_paths.read_only_paths(entry):
            source_adapter = adapter_for_production(source, adapters)
            destination_adapter = adapter_for_production(path, adapters)
            if destination_adapter is None:
                continue
            if (
                source_adapter is None
                or source_adapter.get("platform_root") != destination_adapter.get("platform_root")
            ):
                add(checks, "copy.source-identity", FAIL, "copy source/destination must share selected adapter ownership", source)
                continue
            try:
                path_ownership.validate_platform_writable_path(
                    repo, source_adapter, source, require_existing=True
                )
            except path_ownership.PathOwnershipError as error:
                add(checks, "copy.source-identity", FAIL, str(error), source)
                continue
            if not change_paths.worktree_source_unchanged(repo, source):
                add(checks, "copy.source-identity", FAIL, "copy source must remain an unchanged regular tracked file", source)
            else:
                add(checks, "copy.source-identity", PASS, "copy source is an unchanged safe read-only identity peer", source)

        for candidate in candidates:
            invalid_root = next(
                (root for root in adapter_errors if path_under(candidate, [root])), None
            )
            if invalid_root:
                add(
                    checks, "platform.adapter", FAIL,
                    f"{invalid_root} adapter is missing or invalid", candidate,
                )
                production_seen = True
                continue
            candidate_adapter = adapter_for_production(candidate, adapters)
            if not candidate_adapter:
                continue
            production_seen = True
            try:
                path_ownership.validate_platform_writable_path(repo, candidate_adapter, candidate)
            except path_ownership.PathOwnershipError as error:
                add(checks, "path.production-ownership", FAIL, str(error), candidate)
                continue
            trails = task_trails(repo, candidate_adapter, candidate, changed_paths)
            trails.extend(archived_task_trails(repo, candidate_adapter, candidate, changed_paths))
            receipt_trail = reconcile_receipt_trail(reconcile_receipt, candidate_adapter, candidate)
            if receipt_trail:
                trails.append(receipt_trail)
            trail, owner_packages = select_package_trail(trails)
            if len(owner_packages) > 1:
                add(
                    checks, "trail.production-owner", FAIL,
                    "production path has ambiguous active package owners: " + ", ".join(owner_packages),
                    candidate,
                )
                continue
            if not trail:
                add(
                    checks, "trail.production-task", FAIL,
                    "production path is not covered by an active or archived verified task; "
                    "before staging run reconcile-implementation with an explicit --path",
                    candidate,
                )
                continue
            trails_by_platform.setdefault(str(candidate_adapter["platform_root"]), []).append(trail)
            if not (trail["done"] and trail["evidence"]):
                add(checks, "trail.production-task", UNKNOWN, f"{trail['task']} is pending or lacks staged evidence", candidate)
            else:
                if trail.get("source") == "archived-package":
                    source = "verified archive package receipt"
                else:
                    source = "archived receipt" if trail.get("source") == "archived" else "staged evidence"
                add(checks, "trail.production-task", PASS, f"covered by completed {trail['task']} with {source}", candidate)
            candidate_profile = candidate_adapter["pre_commit"]
            categories = []
            for category, key in (
                ("security", "security_sensitive_globs"),
                ("ui", "ui_globs"), ("localization", "localization_globs"),
            ):
                if glob_match(candidate, list(candidate_profile[key])):
                    categories.append(category)
            if categories and not (trail["done"] and trail["evidence"]):
                add(checks, "platform.runtime-evidence", UNKNOWN, f"{','.join(categories)} evidence is not staged", candidate)
            elif categories:
                add(checks, "platform.runtime-evidence", PASS, f"{','.join(categories)} task evidence is staged", candidate)

        blob, mode = staged_blob(repo, path)
        if entry.status != "D" and blob is not None:
            if mode == "120000":
                if adapter_for_production(path, adapters):
                    add(checks, "path.symlink", FAIL, "platform production writable path may not be a symlink", path)
                target = blob.decode("utf-8", errors="replace")
                if target.startswith("/") or ".." in PurePosixPath(target).parts:
                    add(checks, "path.symlink", FAIL, "symlink target escapes repository", path)
            elif b"\0" not in blob[:8192]:
                if CONFLICT_RE.search(blob):
                    add(checks, "content.conflict-marker", FAIL, "conflict marker in staged blob", path)
                if any(pattern.search(blob) for pattern in DEBUG_PATTERNS):
                    add(checks, "content.debug-leak", FAIL, "debug/investigation marker in staged blob", path)
                if any(pattern.search(blob) for pattern in SECRET_PATTERNS):
                    add(checks, "content.secret-like", FAIL, "secret-like content detected; value suppressed", path)
                if active_spec(path) and PLACEHOLDER_RE.search(blob):
                    add(checks, "spec.active-placeholder", FAIL, "placeholder in active specification artifact", path)

    if production_seen:
        for adapter in adapters:
            root = str(adapter["platform_root"])
            trails = trails_by_platform.get(root, [])
            if not trails:
                continue
            profile = adapter["pre_commit"]
            discoverable_paths = indexed_paths | changed_paths
            discovered_project = any(
                glob_match(candidate, list(profile["project_globs"]))
                for candidate in discoverable_paths
            )
            discovered_tools = sorted(
                tool for tool, globs in profile["tool_globs"].items()
                if any(glob_match(candidate, list(globs)) for candidate in discoverable_paths)
            )
            platform = str(adapter["platform_name"])
            if discovered_project:
                archived_terminal = all(
                    trail.get("source") in {"archived", "archived-package"}
                    and trail.get("done")
                    and trail.get("evidence")
                    for trail in trails
                )
                if archived_terminal:
                    add(checks, f"platform.{platform}.project", PASS, "verified archive receipt covers discovered project/tool evidence")
                elif not discovered_tools or any(not trail["command"] or not trail["evidence"] for trail in trails):
                    add(checks, f"platform.{platform}.project", UNKNOWN, "project/tool discovery requires task command and staged result evidence")
                else:
                    add(checks, f"platform.{platform}.project", PASS, f"task command/result evidence covers discovered tools: {','.join(discovered_tools)}")
            else:
                add(checks, f"platform.{platform}.project", NA, "greenfield: no project configuration discovered")
    else:
        add(checks, "platform.obligations", NA, "no platform production paths staged")

    if harness_seen:
        status, detail = run_staged_harness_lint(repo)
        add(checks, "harness.lint", status, detail)

    after = staged_fingerprint(repo)
    if before != after:
        add(checks, "staged.fingerprint-stable", FAIL, "staged index changed during gate")
    else:
        add(checks, "staged.fingerprint-stable", PASS, "staged fingerprint remained stable")
    statuses = {item["status"] for item in checks}
    overall = FAIL if FAIL in statuses else UNKNOWN if UNKNOWN in statuses else PASS
    return {"status": overall, "fingerprint": after, "checks": checks}


def coverage_report(repo: Path, paths: list[str]) -> dict[str, object]:
    adapters, adapter_errors = load_adapter_state(repo); checks: list[dict[str, str]] = []
    for path in paths:
        value = PurePosixPath(path)
        if value.is_absolute() or ".." in value.parts:
            add(checks, "trail.path", FAIL, "unsafe path", path); continue
        invalid_root = next((root for root in adapter_errors if path_under(path, [root])), None)
        if invalid_root:
            add(checks, "trail.path", FAIL, f"{invalid_root} adapter is missing or invalid", path); continue
        protected_owner = next((
            adapter for adapter in adapters
            if path_under(path, [str(item) for item in adapter["protected_roots"] + adapter["production_exclusions"]])
        ), None)
        if protected_owner:
            add(checks, "trail.path", FAIL, "path is protected from production edits", path); continue
        adapter = adapter_for_production(path, adapters)
        if not adapter:
            add(checks, "trail.path", NA, "path is not platform production", path); continue
        try:
            path_ownership.validate_platform_writable_path(repo, adapter, path)
        except path_ownership.PathOwnershipError as error:
            add(checks, "trail.path", FAIL, str(error), path); continue
        trails = worktree_task_trails(repo, adapter, path)
        packages = sorted(set(str(item["package"]) for item in trails))
        if len(packages) > 1:
            add(
                checks, "trail.path", FAIL,
                "ambiguous active package owners: " + ", ".join(packages), path,
            )
            continue
        trail = trails[0] if trails else None
        profile = adapter["pre_commit"]
        scoped_surface = glob_match(path, list(profile["security_sensitive_globs"]) + list(profile["project_globs"]))
        valid = bool(trail) and (not scoped_surface or bool(trail["scopes"]))
        detail = (
            f"covered by {trail['task']}" if valid
            else "active task with engineering scopes is required" if trail and scoped_surface
            else "no active or archived verified task covers path; run reconcile-implementation with an explicit --path before staging"
        )
        add(checks, "trail.path", PASS if valid else FAIL, detail, path)
    overall = FAIL if any(item["status"] == FAIL for item in checks) else PASS
    return {"status": overall, "checks": checks}


def emit(report: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return
    print(f"Pre-commit: {report['status']}")
    if report.get("fingerprint"):
        print(f"Staged fingerprint: {report['fingerprint']}")
    for item in report["checks"]:
        location = f" [{item['path']}]" if item.get("path") else ""
        print(f"- {item['status']} {item['id']}{location}: {item['detail']}")


def configure_git(repo: Path) -> None:
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "precommit@example.invalid")
    git(repo, "config", "user.name", "Precommit Test")
    git(repo, "config", "core.filemode", "true")


def fixture_adapter(platform: str) -> dict[str, object]:
    root = platform
    suffix = ".swift" if platform == "iOS" else ".kt"
    return {
        "platform_name": platform, "platform_root": root,
        "package_root": f"{root}/specs", "active_changes_namespace": "changes",
        "archive_namespace": "archive",
        "production_roots": [root],
        "protected_roots": [f"{root}/AGENTS.md", f"{root}/specs", f"{root}/workflow"],
        "production_exclusions": [f"{root}/AGENTS.md", f"{root}/specs", f"{root}/workflow"],
        "pre_commit": {
            "source_suffixes": [suffix],
            "generated_globs": [f"{root}/**/build/**"],
            "secret_globs": [f"{root}/**/*.key"],
            "security_sensitive_globs": [f"{root}/**/Security.*"],
            "ui_globs": [f"{root}/**/*View{suffix}"],
            "localization_globs": [f"{root}/**/Localizable.*"],
            "project_globs": [f"{root}/**/Project.config"],
            "tool_globs": {"build-tool": [f"{root}/**/Project.config"]},
        },
    }


def write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); configure_git(repo)
        write(repo / "README.md", "base\n"); git(repo, "add", "README.md"); git(repo, "commit", "-qm", "base")
        assert evaluate(repo)["status"] == FAIL

        write(repo / "notes.md", "safe staged\n"); git(repo, "add", "notes.md")
        write(repo / "notes.md", "safe staged\npassword = 'worktree-only-secret-value'\n")
        safe = evaluate(repo); assert safe["status"] == PASS
        first_fingerprint = safe["fingerprint"]
        git(repo, "add", "notes.md")
        leaked = evaluate(repo)
        assert leaked["status"] == FAIL and leaked["fingerprint"] != first_fingerprint
        rendered = json.dumps(leaked)
        assert "worktree-only-secret-value" not in rendered
        git(repo, "reset", "-q", "HEAD", "notes.md"); (repo / "notes.md").unlink()

        write(repo / ".env", "SAFE_FIXTURE=true\n"); git(repo, "add", ".env")
        assert evaluate(repo)["status"] == FAIL
        git(repo, "reset", "-q", "HEAD", ".env"); (repo / ".env").unlink()

        write(repo / "conflict.txt", "<<<<<<< ours\nx\n=======\ny\n>>>>>>> theirs\n")
        git(repo, "add", "conflict.txt"); assert evaluate(repo)["status"] == FAIL
        git(repo, "reset", "-q", "HEAD", "conflict.txt"); (repo / "conflict.txt").unlink()
        write(repo / "build/output.log", "noise\n"); git(repo, "add", "-f", "build/output.log")
        assert evaluate(repo)["status"] == FAIL
        git(repo, "reset", "-q", "HEAD", "build/output.log")
        (repo / "build/output.log").unlink()

        write(repo / "specs/product/README.md", "Path example: specs/product/<feature>/spec.md\n")
        git(repo, "add", "specs/product/README.md")
        readme_report = evaluate(repo)
        assert readme_report["status"] == PASS, readme_report
        assert not active_spec("specs/product/README.md")
        git(repo, "reset", "-q", "HEAD", "specs/product/README.md")
        (repo / "specs/product/README.md").unlink()
        write(repo / "specs/product/sample/spec.md", "TODO active\n")
        git(repo, "add", "specs/product/sample/spec.md"); assert evaluate(repo)["status"] == FAIL
        assert active_spec("specs/product/sample/spec.md")
        git(repo, "reset", "-q", "HEAD", "specs/product/sample/spec.md")
        (repo / "specs/product/sample/spec.md").unlink()
        write(repo / "workflow/templates/sample.md", "TODO template\n")
        git(repo, "add", "workflow/templates/sample.md")
        # Harness lint is intentionally unavailable in this minimal fixture, so
        # template exclusion is asserted directly rather than through overall status.
        assert not active_spec("workflow/templates/sample.md")
        git(repo, "reset", "-q", "HEAD", "workflow/templates/sample.md")
        (repo / "workflow/templates/sample.md").unlink()

        write(repo / "binary.bin", b"\x00\x01\x02")
        os.symlink("binary.bin", repo / "safe-link")
        git(repo, "add", "binary.bin", "safe-link")
        assert evaluate(repo)["status"] == PASS
        git(repo, "reset", "-q", "HEAD", "binary.bin", "safe-link")
        (repo / "binary.bin").unlink(); (repo / "safe-link").unlink()

        write(repo / "tracked.txt", "old\n"); git(repo, "add", "tracked.txt"); git(repo, "commit", "-qm", "tracked")
        (repo / "tracked.txt").rename(repo / "renamed.txt"); git(repo, "add", "-A")
        rename_report = evaluate(repo)
        assert rename_report["status"] == PASS, rename_report
        assert evaluate(
            repo, ["tracked.txt", "renamed.txt"], require_intended=True
        )["status"] == PASS
        assert evaluate(repo, ["renamed.txt"], require_intended=True)["status"] == FAIL
        git(repo, "reset", "-q", "--hard", "HEAD")
        write(repo / "unrelated.tmp", "untracked owner state\n")
        before_untracked = (repo / "unrelated.tmp").read_text()
        write(repo / "safe.md", "safe\n"); git(repo, "add", "safe.md"); assert evaluate(repo)["status"] == PASS
        assert evaluate(repo, ["safe.md"], require_intended=True)["status"] == PASS
        assert evaluate(repo, ["missing.md"], require_intended=True)["status"] == FAIL
        assert evaluate(repo, ["../escape"], require_intended=True)["status"] == FAIL
        write(repo / "foreign.md", "foreign staged\n"); git(repo, "add", "foreign.md")
        assert evaluate(repo, ["safe.md"], require_intended=True)["status"] == FAIL
        git(repo, "reset", "-q", "HEAD", "foreign.md"); (repo / "foreign.md").unlink()
        assert (repo / "unrelated.tmp").read_text() == before_untracked
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); configure_git(repo)
        write(repo / "README.md", "base\n"); git(repo, "add", "README.md"); git(repo, "commit", "-qm", "base")
        write(repo / "delivery.md", "exact staged delivery\n"); git(repo, "add", "delivery.md")
        assert hook_evaluate(repo, consume=False)["status"] == FAIL
        exact = canonical_evaluate(repo, ["delivery.md"])
        assert exact["status"] == PASS
        target = receipt_path(repo)
        assert stat.S_IMODE(target.parent.stat().st_mode) == RECEIPT_DIRECTORY_MODE
        assert stat.S_IMODE(target.stat().st_mode) == RECEIPT_FILE_MODE
        assert hook_evaluate(repo, consume=False)["status"] == PASS
        assert hook_evaluate(repo, consume=False)["status"] == PASS
        assert hook_evaluate(repo, consume=True)["status"] == PASS
        assert hook_evaluate(repo, consume=True)["status"] == FAIL

        def mutate_receipt(mutator) -> None:
            issue_receipt(repo, ["delivery.md"], staged_fingerprint(repo))
            payload = json.loads(target.read_text(encoding="utf-8"))
            mutator(payload)
            target.write_text(json.dumps(payload), encoding="utf-8")
            os.chmod(target, RECEIPT_FILE_MODE)

        mutate_receipt(lambda payload: payload.update(repo="/wrong/repository"))
        assert hook_evaluate(repo, consume=True)["status"] == FAIL
        mutate_receipt(lambda payload: payload.update(fingerprint="0" * 64))
        assert hook_evaluate(repo, consume=True)["status"] == FAIL
        mutate_receipt(lambda payload: payload.update(intended_paths=["foreign.md"]))
        assert hook_evaluate(repo, consume=True)["status"] == FAIL
        mutate_receipt(
            lambda payload: payload.update(
                created_at=time.time() - RECEIPT_TTL_SECONDS - 10,
                expires_at=time.time() - 10,
            )
        )
        assert hook_evaluate(repo, consume=True)["status"] == FAIL
        issue_receipt(repo, ["delivery.md"], staged_fingerprint(repo))
        target.write_text("{ malformed\n", encoding="utf-8"); os.chmod(target, RECEIPT_FILE_MODE)
        assert hook_evaluate(repo, consume=True)["status"] == FAIL
        for constant in ("NaN", "Infinity", "-Infinity"):
            issue_receipt(repo, ["delivery.md"], staged_fingerprint(repo))
            body = target.read_text(encoding="utf-8")
            body = re.sub(r'"created_at":[^,]+', f'"created_at":{constant}', body)
            target.write_text(body, encoding="utf-8"); os.chmod(target, RECEIPT_FILE_MODE)
            assert hook_evaluate(repo, consume=True)["status"] == FAIL
        mutate_receipt(lambda payload: payload.update(created_at=True))
        assert hook_evaluate(repo, consume=True)["status"] == FAIL
        issue_receipt(repo, ["delivery.md"], staged_fingerprint(repo)); os.chmod(target, 0o644)
        assert hook_evaluate(repo, consume=False)["status"] == FAIL
        target.unlink()
        link_target = repo / "receipt-link-target.json"; link_target.write_text("{}\n", encoding="utf-8")
        target.symlink_to(link_target)
        assert hook_evaluate(repo, consume=False)["status"] == FAIL
        target.unlink(); link_target.unlink()
        issue_receipt(repo, ["delivery.md"], staged_fingerprint(repo))
        os.chmod(target.parent, 0o755)
        assert hook_evaluate(repo, consume=False)["status"] == FAIL
        os.chmod(target.parent, RECEIPT_DIRECTORY_MODE); target.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); configure_git(repo)
        for platform in ("iOS", "Android"):
            write(repo / f"{platform}/workflow/platform-contract.json", json.dumps(fixture_adapter(platform)))
        write(repo / "README.md", "fixture\n")
        git(repo, "add", "."); git(repo, "commit", "-qm", "adapters")
        fixture_adapters = load_adapters(repo, from_index=True)
        for platform in ("iOS", "Android"):
            agents_path = f"{platform}/AGENTS.md"
            assert adapter_for_production(agents_path, fixture_adapters) is None
            assert any(
                agents_path == prefix or agents_path.startswith(prefix)
                for prefix in HARNESS_PREFIXES
            )

        for platform, source in (("iOS", "Sample.swift"), ("Android", "Sample.kt")):
            package = repo / f"{platform}/specs/sample/changes/sample"
            write(package / "meta.json", json.dumps({"status": "implementing"}))
            write(
                package / "plan/task-001.md",
                f"# task\n- Engineering scopes: [\"application\"]\n"
                f"- Paths: proposed: {platform}/App/{source}; proposed: {platform}/App/Project.config\n"
                "- Status: pending\n- Evidence: none\n- Discovered command: build-tool verify\n",
            )
            write(repo / f"{platform}/App/{source}", f"safe {platform} source\n")
            write(repo / f"{platform}/App/Project.config", f"{platform} project fixture\n")
            git(repo, "add", f"{platform}/specs", f"{platform}/App")
            pending = evaluate(repo)
            assert pending["status"] == UNKNOWN, pending
            write(
                package / "plan/task-001.md",
                f"# task\n- Engineering scopes: [\"application\"]\n"
                f"- Paths: proposed: {platform}/App/{source}; proposed: {platform}/App/Project.config\n"
                "- Status: done\n- Evidence: evidence/task-001.md\n- Discovered command: build-tool verify\n",
            )
            write(package / "evidence/task-001.md", "focused runtime command result\n")
            git(repo, "add", f"{platform}/specs")
            report = evaluate(repo)
            assert report["status"] == PASS, report
            sibling = repo / f"{platform}/App/Uncovered{Path(source).suffix}"
            write(sibling, "unsafe sibling\n"); git(repo, "add", sibling.relative_to(repo).as_posix())
            uncovered = evaluate(repo)
            assert uncovered["status"] == FAIL
            assert any(item.get("path") == sibling.relative_to(repo).as_posix() for item in uncovered["checks"])
            assert any("reconcile-implementation" in item.get("detail", "") for item in uncovered["checks"])
            git(repo, "reset", "-q", "HEAD", sibling.relative_to(repo).as_posix()); sibling.unlink()
            git(repo, "commit", "-qm", f"{platform.lower()} fixture")

            package = repo / f"{platform}/specs/sample/changes/sample"
            archive = repo / f"{platform}/specs/sample/archive/2026-07-17-sample"
            shutil.move(str(package), str(archive))
            meta_path = archive / "meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta.update(
                status="archived",
                archived_path=archive.relative_to(repo).as_posix(),
                verification_status="PASS",
                tasks_total=1,
                tasks_done=1,
            )
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            write(
                archive / "archive-receipt.json",
                json.dumps({
                    "schema_version": 2,
                    "mode": "implementation",
                    "platform": platform,
                    "feature": "sample",
                    "change_id": "sample",
                    "archived_path": archive.relative_to(repo).as_posix(),
                    "verification_status": "PASS",
                    "tasks_total": 1,
                    "tasks_done": 1,
                }),
            )
            write(
                package / "ARCHIVED.md",
                "# Archived implementation change\n\n"
                f"- Platform: {platform}\n- Feature: sample\n- Change ID: sample\n"
                f"- Target: `{archive.relative_to(repo).as_posix()}`\n",
            )
            write(repo / f"{platform}/App/{source}", f"post-archive {platform} source\n")
            git(repo, "add", f"{platform}/specs", f"{platform}/App/{source}")
            post_archive = evaluate(repo)
            assert post_archive["status"] == PASS, post_archive
            assert any(
                item["id"] == "trail.production-task"
                and item.get("path") == f"{platform}/App/{source}"
                and "archived receipt" in item["detail"]
                for item in post_archive["checks"]
            )
            post_archive_coverage = coverage_report(repo, [f"{platform}/App/{source}"])
            assert post_archive_coverage["status"] == PASS, post_archive_coverage
            git(repo, "reset", "-q", "--hard", "HEAD")

            orphan = repo / f"{platform}/App/Orphan{Path(source).suffix}"
            write(orphan, "tracked without task trail\n")
            git(repo, "add", orphan.relative_to(repo).as_posix())
            git(repo, "commit", "-qm", f"{platform.lower()} orphan baseline")
            orphan.unlink(); git(repo, "add", "-A")
            deleted = evaluate(repo)
            assert deleted["status"] == FAIL
            assert any(item.get("path") == orphan.relative_to(repo).as_posix() for item in deleted["checks"])
            git(repo, "reset", "-q", "--hard", "HEAD")
            moved = orphan.with_name(f"Moved{Path(source).suffix}")
            orphan.rename(moved); git(repo, "add", "-A")
            renamed = evaluate(repo)
            assert renamed["status"] == FAIL
            rename_paths = {item.get("path") for item in renamed["checks"]}
            assert orphan.relative_to(repo).as_posix() in rename_paths
            assert moved.relative_to(repo).as_posix() in rename_paths
            git(repo, "reset", "-q", "--hard", "HEAD")
            copied = orphan.with_name(f"Copied{Path(source).suffix}")
            write(copied, orphan.read_bytes()); git(repo, "add", copied.relative_to(repo).as_posix())
            source_baseline = orphan.read_bytes()
            orphan.write_text("staged source mutation\n", encoding="utf-8"); git(repo, "add", orphan.relative_to(repo).as_posix())
            orphan.write_bytes(source_baseline)
            copy_identity = sorted([orphan.relative_to(repo).as_posix(), copied.relative_to(repo).as_posix()])
            assert evaluate(repo, copy_identity, require_intended=True)["status"] == FAIL
            git(repo, "reset", "-q", "HEAD", "--", orphan.relative_to(repo).as_posix())
            orphan.chmod(0o755); git(repo, "add", orphan.relative_to(repo).as_posix()); orphan.chmod(0o644)
            assert evaluate(repo, copy_identity, require_intended=True)["status"] == FAIL
            git(repo, "reset", "-q", "HEAD", "--", orphan.relative_to(repo).as_posix())
            git(repo, "rm", "--cached", "-q", "--", orphan.relative_to(repo).as_posix())
            assert evaluate(repo, copy_identity, require_intended=True)["status"] == FAIL
            git(repo, "reset", "-q", "HEAD", "--", orphan.relative_to(repo).as_posix())
            copy_entries = staged_entries(repo)
            normalized_copy, copy_errors = change_paths.normalize_for_intent(
                repo, copy_entries, copy_identity, staged=True
            )
            assert copy_errors == []
            assert any(
                entry.status == "C" and entry.old_path == orphan.relative_to(repo).as_posix()
                for entry in normalized_copy
            )
            assert evaluate(repo, [copied.relative_to(repo).as_posix()], require_intended=True)["status"] == FAIL
            assert evaluate(repo, [orphan.relative_to(repo).as_posix()], require_intended=True)["status"] == FAIL
            copied_report = evaluate(repo, copy_identity, require_intended=True)
            assert copied_report["status"] == FAIL
            copy_paths = {item.get("path") for item in copied_report["checks"]}
            assert orphan.relative_to(repo).as_posix() in copy_paths
            assert copied.relative_to(repo).as_posix() in copy_paths
            git(repo, "reset", "-q", "--hard", "HEAD")

        duplicate = repo / "iOS/specs/duplicate/changes/second"
        write(duplicate / "meta.json", json.dumps({"status": "implementing"}))
        write(
            duplicate / "plan/task-001.md",
            "# duplicate owner\n- Engineering scopes: [\"application\"]\n"
            "- Paths: existing: iOS/App/Sample.swift\n- Status: done\n"
            "- Evidence: evidence/task-001.md\n- Discovered command: build-tool verify\n",
        )
        write(duplicate / "evidence/task-001.md", "duplicate proof\n")
        ios_source = repo / "iOS/App/Sample.swift"
        write(ios_source, "ambiguous owner mutation\n")
        git(repo, "add", "iOS/specs/duplicate", "iOS/App/Sample.swift")
        ambiguous_owner = evaluate(repo)
        assert ambiguous_owner["status"] == FAIL
        assert any(item["id"] == "trail.production-owner" for item in ambiguous_owner["checks"])
        git(repo, "reset", "-q", "--hard", "HEAD")

        ios_source = repo / "iOS/App/Sample.swift"
        write(ios_source, "adapter mutation\n"); git(repo, "add", ios_source.relative_to(repo).as_posix())
        write(repo / "iOS/workflow/platform-contract.json", "{ malformed\n")
        git(repo, "add", "iOS/workflow/platform-contract.json")
        malformed = evaluate(repo)
        assert malformed["status"] == FAIL
        assert any(item["id"] == "platform.adapter" and item.get("path") == "iOS/App/Sample.swift" for item in malformed["checks"])
        git(repo, "reset", "-q", "--hard", "HEAD")
        android_source = repo / "Android/App/Sample.kt"
        write(android_source, "missing adapter mutation\n"); git(repo, "add", android_source.relative_to(repo).as_posix())
        (repo / "Android/workflow/platform-contract.json").unlink(); git(repo, "add", "-A")
        missing_adapter = evaluate(repo)
        assert missing_adapter["status"] == FAIL
        assert any(item["id"] == "platform.adapter" and item.get("path") == "Android/App/Sample.kt" for item in missing_adapter["checks"])
        git(repo, "reset", "-q", "--hard", "HEAD")

        assert coverage_report(repo, ["../escape"])["status"] == FAIL
        assert coverage_report(repo, ["iOS/workflow/rules/new.md"])["status"] == FAIL
        hint = coverage_report(repo, ["iOS/App/Uncovered.swift"])
        assert any("reconcile-implementation" in item.get("detail", "") for item in hint["checks"])
    print("pre-commit-check self-test: PASS (exact one-shot receipt, index-only, evidence/tools, adapter fail-closed, rename/copy/delete)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--path", action="append", default=[], dest="intended_paths")
    parser.add_argument("--hook", action="store_true", help="generic read-only hook integrity mode")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--path-coverage", action="append", default=[])
    parser.add_argument("--root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    try:
        repo = repository_root(args.root)
    except ValueError as error:
        report = {"status": FAIL, "checks": [{"id": "repository", "status": FAIL, "detail": str(error)}]}
        emit(report, args.as_json); return 2
    if args.path_coverage:
        report = coverage_report(repo, args.path_coverage)
    elif args.staged:
        if args.hook and args.intended_paths:
            parser.error("--hook generic mode does not accept delivery --path binding")
        if args.hook:
            report = hook_evaluate(repo, consume=True)
        else:
            report = canonical_evaluate(repo, args.intended_paths)
    else:
        parser.error("--staged or --path-coverage is required")
    emit(report, args.as_json)
    return 0 if report["status"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
