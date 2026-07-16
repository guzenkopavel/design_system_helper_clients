#!/usr/bin/env python3
"""Inspect and guard explicit pre-delivery implementation reconciliation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


ROUTE_REQUIRED = "ROUTE_REQUIRED"
DRIFT = "DRIFT"
ALIGNED = "ALIGNED"
RECONCILED = "RECONCILED"
INVALID = "INVALID"
CLASSIFICATIONS = {
    "auto", "aligned", "task-drift", "platform-implementation-drift",
    "shared-product-impact", "uncertain",
}
COMMON_META_MUTABLE = {
    "status", "tasks_total", "tasks_done", "verification_status",
    "verified_at", "verification_state", "problems",
}
PLATFORM_DRIFT_META_MUTABLE = COMMON_META_MUTABLE | {
    "engineering_scopes", "applicable_rule_files", "design_gate",
    "rule_selection_snapshot",
}
WRITABLE_PACKAGE_FILES = {
    "implementation-spec.md", "design.md", "verification.md", "meta.json",
    "plan/README.md", "plan/rule-selection.json",
}
RECONCILIATION_EVIDENCE_RE = re.compile(
    r"^evidence/reconciliation-[0-9]{8}T[0-9]{6}Z-task-[0-9]{3}(?:-[a-z0-9-]+)?\.md$"
)
TOKEN_RE = re.compile(r"^[a-f0-9]{32}$")
EXCLUDED_DIRS = {
    ".git", ".build", ".gradle", ".idea", ".kotlin", ".swiftpm",
    "DerivedData", "__pycache__", "build", "node_modules",
}


class ReconcileError(ValueError):
    pass


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ReconcileError(f"cannot load support module: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def support_modules(root: Path):
    del root
    scripts = Path(__file__).resolve().parent
    return (
        load_module(scripts / "validate-platform-change.py", "reconcile_validator"),
        load_module(scripts / "pre-commit-check.py", "reconcile_precommit"),
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)


def repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    result = git(candidate, "rev-parse", "--show-toplevel")
    if result.returncode:
        raise ReconcileError("not inside a Git repository")
    return Path(result.stdout.decode().strip()).resolve()


def safe_path(raw: str) -> str:
    value = PurePosixPath(raw)
    if value.is_absolute() or ".." in value.parts or not value.parts:
        raise ReconcileError(f"intended path must be safe and repo-relative: {raw}")
    normalized = value.as_posix()
    if normalized in {".", ""}:
        raise ReconcileError(f"intended path must name a file: {raw}")
    return normalized


def path_under(raw: str, roots: list[str]) -> bool:
    value = PurePosixPath(raw)
    return any(value == PurePosixPath(root) or PurePosixPath(root) in value.parents for root in roots)


def production_owned(adapter: dict[str, object], raw: str) -> bool:
    roots = [str(item) for item in adapter.get("production_roots", [])]
    excluded = [
        str(item)
        for item in adapter.get("protected_roots", []) + adapter.get("production_exclusions", [])
    ]
    return path_under(raw, roots) and not path_under(raw, excluded)


def worktree_changes(repo: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    raw = git(repo, "diff", "HEAD", "--name-status", "-z", "--find-renames").stdout
    fields = raw.split(b"\0"); index = 0
    while index < len(fields) and fields[index]:
        status_value = fields[index].decode("utf-8", errors="replace"); index += 1
        status_code = status_value[:1]
        if status_code in {"R", "C"}:
            old = fields[index].decode("utf-8", errors="surrogateescape"); index += 1
            new = fields[index].decode("utf-8", errors="surrogateescape"); index += 1
            result[old] = {"status": f"{status_code}-old", "peer": new}
            result[new] = {"status": f"{status_code}-new", "peer": old}
        else:
            path = fields[index].decode("utf-8", errors="surrogateescape"); index += 1
            result[path] = {"status": status_code}
    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout
    for item in untracked.split(b"\0"):
        if item:
            result[item.decode("utf-8", errors="surrogateescape")] = {"status": "A-untracked"}
    deleted = [raw for raw, record in result.items() if record.get("status") == "D"]
    added = [raw for raw, record in result.items() if record.get("status") == "A-untracked"]
    added_by_hash: dict[str, list[str]] = {}
    for raw in added:
        try:
            digest = hashlib.sha256((repo / raw).read_bytes()).hexdigest()
        except OSError:
            continue
        added_by_hash.setdefault(digest, []).append(raw)
    for old in deleted:
        baseline = git(repo, "show", f"HEAD:{old}")
        if baseline.returncode:
            continue
        matches = added_by_hash.get(hashlib.sha256(baseline.stdout).hexdigest(), [])
        if len(matches) == 1:
            new = matches[0]
            result[old] = {"status": "R-old", "peer": new}
            result[new] = {"status": "R-new", "peer": old}
    return result


def index_fingerprint(repo: Path) -> str:
    names = git(repo, "diff", "--cached", "--name-status", "-z", "--find-renames").stdout
    index = git(repo, "ls-files", "-s", "-z").stdout
    diff = git(repo, "diff", "--cached", "--binary", "--no-ext-diff").stdout
    return hashlib.sha256(names + b"\0INDEX\0" + index + b"\0DIFF\0" + diff).hexdigest()


def head_identity(repo: Path) -> dict[str, str]:
    commit = git(repo, "rev-parse", "--verify", "HEAD")
    if commit.returncode:
        raise ReconcileError("repository HEAD commit is unavailable")
    symbolic = git(repo, "symbolic-ref", "-q", "HEAD")
    return {
        "commit": commit.stdout.decode("utf-8", errors="replace").strip(),
        "symbolic": (
            symbolic.stdout.decode("utf-8", errors="replace").strip()
            if symbolic.returncode == 0
            else "DETACHED"
        ),
    }


def file_record(path: Path) -> dict[str, object]:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        payload = os.readlink(path).encode("utf-8", errors="surrogateescape")
        kind = "symlink"
    else:
        payload = path.read_bytes()
        kind = "file"
    return {
        "kind": kind,
        "mode": stat.S_IMODE(info.st_mode),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }


def repository_snapshot(repo: Path) -> dict[str, dict[str, object]]:
    snapshot: dict[str, dict[str, object]] = {}
    for base, dirs, files in os.walk(repo):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(base) / name
            relative = path.relative_to(repo).as_posix()
            try:
                snapshot[relative] = file_record(path)
            except OSError as error:
                raise ReconcileError(f"cannot snapshot repository path: {relative}: {error}") from error
    return snapshot


def changed_snapshot_paths(
    before: dict[str, dict[str, object]], after: dict[str, dict[str, object]]
) -> set[str]:
    return {raw for raw in set(before) | set(after) if before.get(raw) != after.get(raw)}


def task_semantic_body(text: str) -> str:
    lines = [
        line for line in text.splitlines()
        if not re.match(r"^\s*-\s*(?:Status|Evidence):", line, re.IGNORECASE)
    ]
    return "\n".join(lines).strip()


def task_semantic_hashes(package: Path, repo: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted((package / "plan").glob("task-*.md")):
        relative = path.relative_to(repo).as_posix()
        body = task_semantic_body(path.read_text(encoding="utf-8", errors="replace"))
        result[relative] = hashlib.sha256(body.encode()).hexdigest()
    return result


def task_full_hashes(package: Path, repo: Path) -> dict[str, str]:
    return {
        path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((package / "plan").glob("task-*.md"))
        if path.is_file()
    }


def file_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def changed_contracts(package: Path, baseline: dict[str, object], repo: Path) -> set[str]:
    result: set[str] = set()
    recorded = baseline.get("contract_hashes", {})
    if not isinstance(recorded, dict):
        return result
    for raw, before in recorded.items():
        if file_hash(repo / raw) != before:
            result.add(str(raw))
    return result


def task_coverage(
    repo: Path, package: Path, intended: list[str], validator, precommit
) -> tuple[list[dict[str, object]], dict[str, list[str]], set[str], list[str]]:
    tasks, parse_errors = validator.parse_tasks(repo, package)
    coverage: dict[str, list[str]] = {}
    direct: set[str] = set()
    for raw in intended:
        owners: list[str] = []
        for task in tasks:
            if any(precommit.declared_covers(repo, declared, raw) for _kind, declared in task["paths"]):
                task_id = str(task["id"])
                owners.append(task_id)
                direct.add(task_id)
        coverage[raw] = owners
    closure = set(direct)
    changed = True
    while changed:
        changed = False
        for task in tasks:
            task_id = str(task["id"])
            if task_id not in closure and set(str(item) for item in task["deps"]) & closure:
                closure.add(task_id); changed = True
    return tasks, coverage, closure, parse_errors


def reconciliation_next_step(status: object) -> str:
    if status == "verified":
        return "run fresh verify to restore invalidated terminal state before any terminal claim or archive"
    return "scoped staging and pre-commit may proceed after RECONCILED; verify remains the terminal lifecycle step"


def resolve_context(
    repo: Path,
    platform: str,
    feature: str,
    change: str | None,
    intended_raw: list[str],
    classification: str,
) -> dict[str, object]:
    validator, precommit = support_modules(repo)
    if classification not in CLASSIFICATIONS:
        raise ReconcileError(f"unknown classification: {classification}")
    try:
        adapter = validator.load_adapter(repo, platform)
        validator.require_capability(adapter, "implement")
        change_id, package = validator.resolve_change(repo, adapter, feature, change, "implement")
    except (ValueError, OSError) as error:
        return {
            "outcome": ROUTE_REQUIRED,
            "route": "resolve an unambiguous active platform package before reconciliation",
            "errors": [str(error)],
        }
    meta_path = package / "meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"outcome": ROUTE_REQUIRED, "route": "repair package identity/state", "errors": [str(error)]}
    if meta.get("status") == "archived" or (package / "ARCHIVED.md").is_file():
        return {"outcome": ROUTE_REQUIRED, "route": "start a new change; archived packages are immutable", "errors": []}
    status = meta.get("status")
    if status in {"draft", "specified"}:
        route = "complete Propose before reconciliation" if status == "draft" else "complete Plan before reconciliation"
        return {"outcome": ROUTE_REQUIRED, "route": route, "errors": [], "current_state": {"status": status}}
    if status not in {"planned", "implementing", "verified"}:
        return {"outcome": ROUTE_REQUIRED, "route": "restore a supported planned/implementing/verified package state", "errors": []}
    if meta.get("verification_status") in {"FAIL", "UNKNOWN"}:
        return {
            "outcome": ROUTE_REQUIRED,
            "route": "run canonical $implement recovery for existing FAIL/UNKNOWN verification state",
            "errors": [],
            "current_state": {
                "status": status,
                "verification_status": meta.get("verification_status"),
                "problems": meta.get("problems"),
            },
        }
    intended: list[str] = []
    try:
        intended = sorted(set(safe_path(raw) for raw in intended_raw))
    except ReconcileError as error:
        return {"outcome": ROUTE_REQUIRED, "route": "provide safe explicit intended paths", "errors": [str(error)]}
    if not intended:
        return {"outcome": ROUTE_REQUIRED, "route": "provide at least one explicit --path", "errors": []}
    changes = worktree_changes(repo)
    errors: list[str] = []
    for raw in intended:
        if not production_owned(adapter, raw):
            errors.append(f"path is outside selected platform production ownership: {raw}")
        if raw not in changes:
            errors.append(f"intended path has no current worktree/index change: {raw}")
    for raw in intended:
        record = changes.get(raw, {})
        peer = record.get("peer")
        if isinstance(peer, str) and peer not in intended:
            errors.append(f"rename/copy requires both explicit sides: {raw} -> {peer}")
    if errors:
        return {"outcome": ROUTE_REQUIRED, "route": "correct the explicit intended set", "errors": sorted(set(errors))}
    if classification in {"shared-product-impact", "uncertain"}:
        route = "discovery/elaborate; approved shared product behavior and approval remain immutable"
        return {
            "outcome": ROUTE_REQUIRED, "route": route, "errors": [],
            "platform": adapter["platform_name"], "feature": feature, "change": change_id,
            "intended_paths": intended,
        }
    tasks, coverage, closure, parse_errors = task_coverage(repo, package, intended, validator, precommit)
    uncovered = sorted(raw for raw, owners in coverage.items() if not owners)
    if classification in {"task-drift", "platform-implementation-drift"} or uncovered or parse_errors:
        outcome = DRIFT
    else:
        outcome = ALIGNED
    return {
        "outcome": outcome,
        "semantic_judgment_required": classification == "auto",
        "classification": classification,
        "platform": adapter["platform_name"],
        "platform_input": adapter["platform_input"],
        "feature": feature,
        "change": change_id,
        "package": package.relative_to(repo).as_posix(),
        "intended_paths": intended,
        "path_status": {raw: changes[raw] for raw in intended},
        "task_coverage": coverage,
        "affected_task_closure": sorted(closure),
        "uncovered_paths": uncovered,
        "task_parse_errors": parse_errors,
        "current_state": {
            "status": meta.get("status"),
            "verification_status": meta.get("verification_status"),
            "problems": meta.get("problems"),
            "verified_at": meta.get("verified_at"),
            "verification_state": meta.get("verification_state"),
        },
        "requires_focused_evidence": True,
        "required_next_step": reconciliation_next_step(meta.get("status")),
        "_adapter": adapter,
        "_package_path": package,
        "_meta": meta,
        "_validator": validator,
        "_precommit": precommit,
        "_tasks": tasks,
    }


def public_report(context: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in context.items() if not key.startswith("_")}


def state_directory() -> Path:
    path = Path(tempfile.gettempdir()) / "mobile-harness-reconciliation"
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def state_path(token: str) -> Path:
    if not TOKEN_RE.fullmatch(token):
        raise ReconcileError("invalid reconciliation token")
    return state_directory() / f"{token}.json"


def write_state(value: dict[str, object]) -> str:
    token = secrets.token_hex(16)
    path = state_path(token)
    payload = (json.dumps(value, sort_keys=True) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)
    return token


def read_state(token: str) -> tuple[dict[str, object], Path]:
    path = state_path(token)
    info = path.lstat()
    if stat.S_IMODE(info.st_mode) != 0o600 or not stat.S_ISREG(info.st_mode):
        raise ReconcileError("reconciliation state permissions/type are invalid")
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_size > 10 * 1024 * 1024:
                raise ReconcileError("reconciliation state size/type is invalid")
            payload = os.read(descriptor, opened.st_size + 1)
        finally:
            os.close(descriptor)
        value = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ReconcileError("reconciliation state is malformed") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ReconcileError("reconciliation state schema is invalid")
    return value, path


def contract_hashes(repo: Path, package: Path, meta: dict[str, object], adapter: dict[str, object]) -> dict[str, str | None]:
    paths = [
        package / "implementation-spec.md", package / "design.md",
        package / "verification.md", package / "plan/README.md",
        package / "plan/rule-selection.json",
    ]
    for raw in meta.get("applicable_rule_files", []):
        if isinstance(raw, str): paths.append(repo / raw)
    shared = meta.get("shared_product_spec")
    if isinstance(shared, str): paths.append(repo / shared)
    return {path.relative_to(repo).as_posix(): file_hash(path) for path in paths}


def start_guard(context: dict[str, object], repo: Path) -> dict[str, object]:
    if context.get("outcome") == ROUTE_REQUIRED:
        return public_report(context)
    classification = context.get("classification")
    if classification == "auto":
        return {
            **public_report(context),
            "outcome": ROUTE_REQUIRED,
            "route": "record semantic classification before starting reconciliation writes",
        }
    package = context["_package_path"]
    meta = context["_meta"]
    adapter = context["_adapter"]
    snapshot = repository_snapshot(repo)
    evidence_root = package / "evidence"
    existing_evidence = sorted(
        path.relative_to(repo).as_posix()
        for path in evidence_root.rglob("*") if path.is_file()
    ) if evidence_root.is_dir() else []
    state = {
        "schema_version": 1,
        "repo": str(repo),
        "git_dir": str((repo / ".git").resolve()),
        "platform_input": context["platform_input"],
        "feature": context["feature"],
        "change": context["change"],
        "package": context["package"],
        "classification": classification,
        "outcome_before": context["outcome"],
        "intended_paths": context["intended_paths"],
        "intended_status": context["path_status"],
        "affected_task_closure": context["affected_task_closure"],
        "head_identity": head_identity(repo),
        "index_fingerprint": index_fingerprint(repo),
        "snapshot": snapshot,
        "meta": meta,
        "existing_evidence": existing_evidence,
        "task_semantic_hashes": task_semantic_hashes(package, repo),
        "task_full_hashes": task_full_hashes(package, repo),
        "contract_hashes": contract_hashes(repo, package, meta, adapter),
    }
    token = write_state(state)
    return {**public_report(context), "token": token, "guard_state": "private-0600-outside-repository"}


def allowed_package_mutation(package_raw: str, raw: str, before_exists: bool) -> bool:
    prefix = package_raw.rstrip("/") + "/"
    if not raw.startswith(prefix):
        return False
    inner = raw[len(prefix):]
    if inner in WRITABLE_PACKAGE_FILES or re.fullmatch(r"plan/task-[0-9]{3}\.md", inner):
        return True
    if RECONCILIATION_EVIDENCE_RE.fullmatch(inner) and not before_exists:
        return True
    return False


def verification_rows_pending(path: Path) -> bool:
    if not path.is_file():
        return False
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|") or "---" in line or "Status" in line:
            continue
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        if len(cells) >= 5:
            rows.append(cells[-1])
    return bool(rows) and all(value == "pending" for value in rows)


def reconciliation_evidence_valid(
    repo: Path, package: Path, task: dict[str, object], intended: list[str], baseline_evidence: set[str]
) -> tuple[bool, str]:
    evidence = str(task.get("evidence", "none"))
    if not RECONCILIATION_EVIDENCE_RE.fullmatch(evidence):
        return False, f"{task['id']} requires a uniquely named reconciliation evidence file"
    path = package / evidence
    relative = path.relative_to(repo).as_posix()
    if relative in baseline_evidence or not path.is_file() or not path.read_text(encoding="utf-8", errors="ignore").strip():
        return False, f"{task['id']} reconciliation evidence must be new and non-empty"
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "Reconciliation paths:" not in text or "Command:" not in text:
        return False, f"{task['id']} evidence misses paths/command/result fields"
    result_like_lines = []
    for line in text.splitlines():
        normalized = re.sub(r"[*_`]", "", line.strip()).strip()
        if re.match(
            r"^(?:>\s*)?(?:(?:[-+*]|[0-9]+[.)])\s*)?result\s*:",
            normalized,
            re.IGNORECASE,
        ):
            result_like_lines.append(line)
    if result_like_lines != ["- Result: PASS"]:
        return False, f"{task['id']} evidence Result must be the single exact structural field: Result: PASS"
    if any(raw not in text for raw in intended):
        return False, f"{task['id']} evidence misses the triggering intended path set"
    return True, ""


def load_declared_covers(repo: Path, declared: str, raw: str) -> bool:
    value = PurePosixPath(declared.rstrip("/")); candidate = PurePosixPath(raw)
    if value == candidate:
        return True
    target = repo / value
    return (declared.endswith("/") or target.is_dir() or not value.suffix) and value in candidate.parents


def check_guard(token: str) -> dict[str, object]:
    try:
        state, path = read_state(token)
    except (OSError, ReconcileError) as error:
        return {"outcome": INVALID, "errors": [str(error)]}
    try:
        repo = Path(str(state["repo"])).resolve()
        errors: list[str] = []
        if str((repo / ".git").resolve()) != state.get("git_dir"):
            errors.append("repository identity changed")
        if head_identity(repo) != state.get("head_identity"):
            errors.append("repository HEAD/commit identity changed during reconciliation")
        if index_fingerprint(repo) != state.get("index_fingerprint"):
            errors.append("Git index changed during reconciliation")
        before_snapshot = state.get("snapshot", {})
        after_snapshot = repository_snapshot(repo)
        changed = changed_snapshot_paths(before_snapshot, after_snapshot)
        package_raw = str(state["package"])
        intended = [str(item) for item in state.get("intended_paths", [])]
        for raw in sorted(changed):
            if raw in intended:
                errors.append(f"intended production changed during reconciliation: {raw}")
            elif not allowed_package_mutation(package_raw, raw, raw in before_snapshot):
                errors.append(f"write outside reconciliation package scope: {raw}")
        current_changes = worktree_changes(repo)
        current_status = {raw: current_changes.get(raw) for raw in intended}
        if current_status != state.get("intended_status"):
            errors.append("intended rename/delete/content status changed during reconciliation")

        validator, precommit = support_modules(repo)
        try:
            adapter = validator.load_adapter(repo, str(state["platform_input"]))
            change_id, package = validator.resolve_change(
                repo, adapter, str(state["feature"]), str(state["change"]), "implement"
            )
        except (ValueError, OSError) as error:
            errors.append(f"package no longer resolves: {error}")
            package = repo / package_raw
            adapter = {}
            change_id = str(state["change"])
        if package.relative_to(repo).as_posix() != package_raw:
            errors.append("package identity changed")

        baseline_evidence = set(str(item) for item in state.get("existing_evidence", []))
        for raw in baseline_evidence:
            if before_snapshot.get(raw) != after_snapshot.get(raw):
                errors.append(f"historical evidence changed: {raw}")
        proposal = f"{package_raw}/proposal.md"
        if before_snapshot.get(proposal) != after_snapshot.get(proposal):
            errors.append("proposal history changed")

        meta_path = package / "meta.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            meta = {}; errors.append(f"final meta is invalid: {error}")
        baseline_meta = state.get("meta", {})
        classification = str(state.get("classification"))
        allowed_meta = (
            PLATFORM_DRIFT_META_MUTABLE
            if classification == "platform-implementation-drift"
            else COMMON_META_MUTABLE
        )
        if isinstance(baseline_meta, dict):
            changed_meta_fields = {
                key for key in set(baseline_meta) | set(meta)
                if baseline_meta.get(key) != meta.get(key)
            }
            forbidden_meta_fields = sorted(changed_meta_fields - allowed_meta)
            if forbidden_meta_fields:
                errors.append(
                    "reconciliation changed protected meta authority: "
                    + ", ".join(forbidden_meta_fields)
                )
        baseline_status = baseline_meta.get("verification_status") if isinstance(baseline_meta, dict) else None
        if baseline_status in {"FAIL", "UNKNOWN"}:
            if meta.get("verification_status") != baseline_status or meta.get("problems") != baseline_meta.get("problems"):
                errors.append("existing FAIL/UNKNOWN recovery was cleared or blessed")
        if isinstance(baseline_meta, dict) and baseline_meta.get("status") == "verified":
            expected = {
                "status": "implementing", "verification_status": "pending",
                "verified_at": None, "verification_state": None, "problems": [],
            }
            for key, value in expected.items():
                if meta.get(key) != value:
                    errors.append(f"verified package invalidation mismatch: {key}")
            if not verification_rows_pending(package / "verification.md"):
                errors.append("verified package verification rows were not reset to pending")
        if isinstance(baseline_meta, dict) and baseline_meta.get("status") == "planned":
            if meta.get("status") != "implementing":
                errors.append("planned package must become implementing after reconciliation")
        if isinstance(baseline_meta, dict) and baseline_meta.get("status") == "implementing":
            if meta.get("status") != "implementing":
                errors.append("implementing package must remain implementing during reconciliation")

        tasks, coverage, closure, parse_errors = task_coverage(repo, package, intended, validator, precommit)
        errors.extend(f"task parse: {item}" for item in parse_errors)
        for raw, owners in coverage.items():
            if not owners:
                errors.append(f"intended path remains uncovered: {raw}")
        by_id = {str(task["id"]): task for task in tasks}
        required_tasks = set(str(item) for item in state.get("affected_task_closure", [])) | closure
        for task_id in sorted(required_tasks):
            task = by_id.get(task_id)
            if task is None:
                errors.append(f"affected task disappeared during reconciliation: {task_id}")
                continue
            if task.get("status") != "done":
                errors.append(f"affected task is not done after focused reconciliation: {task_id}")
                continue
            valid, detail = reconciliation_evidence_valid(repo, package, task, intended, baseline_evidence)
            if not valid:
                errors.append(detail)

        baseline_contracts = state.get("contract_hashes", {})
        contract_changes = changed_contracts(package, state, repo)
        spec_raw = f"{package_raw}/implementation-spec.md"
        design_raw = f"{package_raw}/design.md"
        verification_raw = f"{package_raw}/verification.md"
        plan_readme_raw = f"{package_raw}/plan/README.md"
        snapshot_raw = f"{package_raw}/plan/rule-selection.json"
        semantic_before = state.get("task_semantic_hashes", {})
        semantic_after = task_semantic_hashes(package, repo)
        semantic_changed_tasks = {
            PurePosixPath(raw).stem
            for raw in set(semantic_before) | set(semantic_after)
            if semantic_before.get(raw) != semantic_after.get(raw)
        }
        allowed_semantic_tasks = (
            set(str(item) for item in state.get("affected_task_closure", [])) | closure
        )
        unrelated_semantic_tasks = sorted(semantic_changed_tasks - allowed_semantic_tasks)
        if unrelated_semantic_tasks:
            errors.append(
                "semantic task changes escape affected/dependent closure: "
                + ", ".join(unrelated_semantic_tasks)
            )
        semantic_tasks_changed = bool(semantic_changed_tasks)
        full_before = state.get("task_full_hashes", {})
        full_after = task_full_hashes(package, repo)
        full_changed_tasks = {
            PurePosixPath(raw).stem
            for raw in set(full_before) | set(full_after)
            if full_before.get(raw) != full_after.get(raw)
        }
        unrelated_full_task_changes = sorted(full_changed_tasks - allowed_semantic_tasks)
        if unrelated_full_task_changes:
            errors.append(
                "task file changes escape affected/dependent closure: "
                + ", ".join(unrelated_full_task_changes)
            )
        if classification == "aligned":
            forbidden = {spec_raw, design_raw, plan_readme_raw, snapshot_raw} & contract_changes
            if forbidden or semantic_tasks_changed:
                errors.append("aligned reconciliation rewrote spec/plan semantics")
            if not (isinstance(baseline_meta, dict) and baseline_meta.get("status") == "verified") and verification_raw in contract_changes:
                errors.append("aligned reconciliation rewrote verification contract")
        elif classification == "task-drift":
            forbidden = {spec_raw, design_raw, verification_raw, snapshot_raw} & contract_changes
            if forbidden:
                errors.append("task drift rewrote platform contracts or rule selection")
            if not semantic_tasks_changed and plan_readme_raw not in changed:
                errors.append("task drift did not repair plan/task semantics")
        elif classification == "platform-implementation-drift":
            required_changes = {spec_raw, design_raw, verification_raw}
            if not required_changes <= changed:
                errors.append("platform implementation drift requires coherent spec/design/verification repair")
            if not semantic_tasks_changed:
                errors.append("platform implementation drift requires coherent task repair")

        if isinstance(baseline_contracts, dict):
            for raw in baseline_contracts:
                if raw.startswith(("workflow/rules/", "iOS/workflow/rules/", "Android/workflow/rules/")):
                    if file_hash(repo / raw) != baseline_contracts[raw]:
                        errors.append(f"rule authority changed: {raw}")
            shared = baseline_meta.get("shared_product_spec") if isinstance(baseline_meta, dict) else None
            if isinstance(shared, str) and file_hash(repo / shared) != baseline_contracts.get(shared):
                errors.append("shared product contract changed")

        if adapter:
            validation_errors = validator.validate_package(
                repo, adapter, str(state["feature"]), change_id, "implement"
            )
            errors.extend(f"final implement validator: {item}" for item in validation_errors)
        result = {
            "outcome": RECONCILED if not errors else INVALID,
            "classification": classification,
            "platform": state.get("platform_input"),
            "feature": state.get("feature"),
            "change": state.get("change"),
            "intended_paths": intended,
            "updated_artifacts": sorted(raw for raw in changed if raw.startswith(package_raw + "/")),
            "evidence_refreshed": sorted(raw for raw in changed if "/evidence/reconciliation-" in raw),
            "required_next_step": reconciliation_next_step(
                baseline_meta.get("status") if isinstance(baseline_meta, dict) else None
            ),
            "errors": sorted(set(errors)),
        }
        return result
    except (OSError, ReconcileError, KeyError, TypeError, ValueError) as error:
        return {"outcome": INVALID, "errors": [str(error)]}
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def emit(report: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(f"Reconciliation: {report.get('outcome', INVALID)}")
    for key in ("platform", "feature", "change", "classification", "required_next_step", "route", "token"):
        if report.get(key) is not None:
            print(f"- {key}: {report[key]}")
    for raw in report.get("intended_paths", []):
        print(f"- intended: {raw}")
    for error in report.get("errors", []):
        print(f"- error: {error}")


def configure_git(repo: Path) -> None:
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "reconcile@example.invalid")
    git(repo, "config", "user.name", "Reconcile Test")


def replace_tree_text(root: Path, old: str, new: str) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            path.write_text(text.replace(old, new), encoding="utf-8")


def write_fixture(repo: Path, platform: str = "iOS") -> tuple[object, dict[str, object], Path, Path]:
    validator = load_module(Path(__file__).with_name("validate-platform-change.py"), f"fixture_validator_{platform}")
    adapter, package, meta = validator.write_fixture(repo)
    source_root = repo / "TestClient"
    target_root = repo / platform
    source_root.rename(target_root)
    replace_tree_text(target_root, "TestClient", platform)
    product = repo / "specs/product/sample/spec.md"
    product.write_text(product.read_text(encoding="utf-8").replace("TestClient", platform), encoding="utf-8")
    adapter_path = target_root / "workflow/platform-contract.json"
    adapter_data = json.loads(adapter_path.read_text(encoding="utf-8"))
    adapter_data = json.loads(json.dumps(adapter_data).replace("TestClient", platform))
    adapter_data["platform_input"] = platform.casefold()
    adapter_data["platform_name"] = platform
    adapter_data["platform_root"] = platform
    adapter_path.write_text(json.dumps(adapter_data), encoding="utf-8")
    package = repo / platform / "specs/sample/changes/sample"
    meta_path = package / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")); meta["platform"] = platform
    meta["applicable_rule_files"] = [raw.replace("TestClient", platform) for raw in meta["applicable_rule_files"]]
    plan = package / "plan"; plan.mkdir()
    source_suffix = ".swift" if platform == "iOS" else ".kt"
    source = repo / platform / "Sources" / f"Sample{source_suffix}"
    source.parent.mkdir(parents=True); source.write_text("baseline\n", encoding="utf-8")
    task = (
        "# task-001 — Reconcile sample\n\n"
        "- Layer: domain\n- Engineering scopes: [\"application\"]\n- Depends on: none\n"
        "- Status: done\n- Evidence: evidence/task-001.md\n- Estimate (ideal): 0.5–1 days\n"
        f"- Paths: existing: {source.relative_to(repo).as_posix()}\n\n"
        "## Goal\nMaintain the typed platform behavior boundary.\n\n"
        "## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes its result.\n\n"
        "## Steps\nKeep the typed boundary aligned with platform contracts.\n\n"
        "## Verification\nRun the focused deterministic boundary test.\n\n"
        "## Expected result\nThe boundary returns the expected typed result.\n\n"
        "## Out of scope\nUnrelated platform cleanup remains excluded.\n"
    )
    (plan / "task-001.md").write_text(task, encoding="utf-8")
    (plan / "README.md").write_text(
        "# Plan\n\n## Planning frame\nMaintain one bounded platform task.\n\n"
        "## Revalidated engineering scopes and exact rules\nApplication scope and exact rules remain selected.\n\n"
        "## DAG\ntask-001 is independent.\n\n## Estimates and multipliers\nOne bounded task.\n\n"
        "## Verification strategy\nRun the focused boundary check.\n",
        encoding="utf-8",
    )
    evidence = package / "evidence"; evidence.mkdir()
    (evidence / "task-001.md").write_text("Historical focused evidence.\n", encoding="utf-8")
    meta.update(
        status="implementing", tasks_total=1, tasks_done=1,
        rule_selection_snapshot="plan/rule-selection.json",
        verification_status="pending", verified_at=None, verification_state=None,
    )
    (plan / "rule-selection.json").write_text(json.dumps(validator.rule_selection_snapshot(meta)), encoding="utf-8")
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    loaded = validator.load_adapter(repo, platform.casefold())
    errors = validator.validate_package(repo, loaded, "sample", "sample", "implement")
    if errors:
        raise AssertionError(errors)
    configure_git(repo); git(repo, "add", "."); git(repo, "commit", "-qm", "fixture")
    source.write_text("intended owner change\n", encoding="utf-8")
    return validator, loaded, package, source


def write_fresh_evidence(
    repo: Path,
    package: Path,
    source: Path,
    suffix: str = "aligned",
    task_id: str = "task-001",
    intended_paths: list[str] | None = None,
) -> None:
    task_path = package / f"plan/{task_id}.md"
    body = task_path.read_text(encoding="utf-8")
    evidence = f"evidence/reconciliation-20260715T120000Z-{task_id}-{suffix}.md"
    body = re.sub(r"(?m)^- Evidence: .+$", f"- Evidence: {evidence}", body)
    task_path.write_text(body, encoding="utf-8")
    paths = intended_paths or [source.relative_to(repo).as_posix()]
    (package / evidence).write_text(
        "# Reconciliation evidence\n\n"
        f"- Reconciliation paths: {', '.join(paths)}\n"
        "- Command: focused fixture check\n- Result: PASS\n",
        encoding="utf-8",
    )


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); validator, adapter, package, source = write_fixture(repo, "iOS")
        uncovered = repo / "iOS/Sources/Uncovered.swift"; uncovered.write_text("new\n", encoding="utf-8")
        report = resolve_context(repo, "ios", "sample", "sample", [uncovered.relative_to(repo).as_posix()], "auto")
        assert report["outcome"] == DRIFT and report["uncovered_paths"]
        context = resolve_context(
            repo, "ios", "sample", "sample",
            [uncovered.relative_to(repo).as_posix()], "task-drift",
        )
        token = str(start_guard(context, repo)["token"])
        task = (package / "plan/task-001.md").read_text(encoding="utf-8")
        task = task.replace("task-001 — Reconcile sample", "task-002 — Cover uncovered path")
        task = task.replace("evidence/task-001.md", "none")
        task = task.replace(source.relative_to(repo).as_posix(), uncovered.relative_to(repo).as_posix())
        (package / "plan/task-002.md").write_text(task, encoding="utf-8")
        plan_readme = package / "plan/README.md"
        plan_readme.write_text(
            plan_readme.read_text(encoding="utf-8").replace(
                "task-001 is independent.",
                "task-001 and task-002 are independent.",
            ),
            encoding="utf-8",
        )
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(tasks_total=2, tasks_done=2); meta_path.write_text(json.dumps(meta), encoding="utf-8")
        write_fresh_evidence(repo, package, uncovered, "uncovered", "task-002")
        assert validator.validate_package(repo, adapter, "sample", "sample", "implement") == []
        uncovered_checked = check_guard(token)
        assert uncovered_checked["outcome"] == RECONCILED, uncovered_checked
        staged_paths = [uncovered.relative_to(repo).as_posix()] + list(uncovered_checked["updated_artifacts"])
        staged = git(repo, "add", "--", *staged_paths)
        assert staged.returncode == 0, staged.stderr.decode("utf-8", errors="replace")
        precommit_report = context["_precommit"].evaluate(repo)
        assert precommit_report["status"] == "PASS", precommit_report
        route = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "shared-product-impact")
        assert route["outcome"] == ROUTE_REQUIRED and not (package / "evidence/reconciliation-route.md").exists()

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); validator, adapter, package, source = write_fixture(repo, "iOS")
        first = package / "plan/task-001.md"
        dependent = first.read_text(encoding="utf-8").replace(
            "task-001 — Reconcile sample", "task-002 — Reconcile dependent"
        ).replace("Depends on: none", "Depends on: task-001").replace(
            "evidence/task-001.md", "evidence/task-002.md"
        ).replace(source.relative_to(repo).as_posix(), "iOS/Sources/Dependent.swift")
        (package / "plan/task-002.md").write_text(dependent, encoding="utf-8")
        (package / "evidence/task-002.md").write_text("Historical dependent evidence.\n", encoding="utf-8")
        dependent_source = repo / "iOS/Sources/Dependent.swift"
        dependent_source.write_text("dependent baseline\n", encoding="utf-8")
        plan_readme = package / "plan/README.md"
        plan_readme.write_text(
            plan_readme.read_text(encoding="utf-8").replace(
                "task-001 is independent.",
                "task-001 is independent. task-002 depends on task-001.",
            ),
            encoding="utf-8",
        )
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(tasks_total=2, tasks_done=2); meta_path.write_text(json.dumps(meta), encoding="utf-8")
        dependent_errors = validator.validate_package(repo, adapter, "sample", "sample", "implement")
        assert dependent_errors == [], dependent_errors
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        assert context["affected_task_closure"] == ["task-001", "task-002"]
        token = str(start_guard(context, repo)["token"])
        write_fresh_evidence(repo, package, source, "closure")
        closure_check = check_guard(token)
        assert closure_check["outcome"] == INVALID
        assert any("task-002" in error for error in closure_check["errors"])

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); validator, adapter, package, source = write_fixture(repo, "iOS")
        first = package / "plan/task-001.md"
        dependent = first.read_text(encoding="utf-8").replace(
            "task-001 — Reconcile sample", "task-002 — Reconcile dependent"
        ).replace("Depends on: none", "Depends on: task-001").replace(
            "evidence/task-001.md", "evidence/task-002.md"
        ).replace(source.relative_to(repo).as_posix(), "iOS/Sources/Dependent.swift")
        (package / "plan/task-002.md").write_text(dependent, encoding="utf-8")
        (package / "evidence/task-002.md").write_text("Historical dependent evidence.\n", encoding="utf-8")
        (repo / "iOS/Sources/Dependent.swift").write_text("dependent baseline\n", encoding="utf-8")
        plan_readme = package / "plan/README.md"
        plan_readme.write_text(
            plan_readme.read_text(encoding="utf-8").replace(
                "task-001 is independent.",
                "task-001 is independent. task-002 depends on task-001.",
            ),
            encoding="utf-8",
        )
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(tasks_total=2, tasks_done=2); meta_path.write_text(json.dumps(meta), encoding="utf-8")
        assert validator.validate_package(repo, adapter, "sample", "sample", "implement") == []
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        token = str(start_guard(context, repo)["token"])
        intended = [source.relative_to(repo).as_posix()]
        write_fresh_evidence(repo, package, source, "closure-direct", "task-001", intended)
        write_fresh_evidence(repo, package, source, "closure-dependent", "task-002", intended)
        closure_positive = check_guard(token)
        assert closure_positive["outcome"] == RECONCILED, closure_positive

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        unrelated = repo / "Android/unrelated.kt"; unrelated.parent.mkdir(); unrelated.write_text("owner state\n", encoding="utf-8")
        staged = repo / "staged-note.md"; staged.write_text("staged owner state\n", encoding="utf-8"); git(repo, "add", "staged-note.md")
        before_index = index_fingerprint(repo)
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        started = start_guard(context, repo); token = str(started["token"])
        state_file = state_path(token); assert stat.S_IMODE(state_file.stat().st_mode) == 0o600
        write_fresh_evidence(repo, package, source)
        checked = check_guard(token)
        assert checked["outcome"] == RECONCILED, checked
        assert index_fingerprint(repo) == before_index
        assert unrelated.read_text(encoding="utf-8") == "owner state\n"
        assert (package / "evidence/task-001.md").read_text(encoding="utf-8") == "Historical focused evidence.\n"

    result_mutations = (
        ("fail", lambda text: text.replace("- Result: PASS", "- Result: FAIL")),
        ("unknown", lambda text: text.replace("- Result: PASS", "- Result: UNKNOWN")),
        ("indented-extra", lambda text: text + "  - Result: FAIL\n"),
        ("duplicate", lambda text: text + "- Result: PASS\n"),
        ("spacing-before-colon", lambda text: text.replace("- Result: PASS", "- Result : PASS")),
        ("spacing-after-colon", lambda text: text.replace("- Result: PASS", "- Result:  PASS")),
        ("case", lambda text: text.replace("- Result: PASS", "- result: PASS")),
        ("decorated", lambda text: text.replace("- Result: PASS", "- **Result:** PASS")),
    )
    for label, mutate_result in result_mutations:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
            context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
            token = str(start_guard(context, repo)["token"])
            write_fresh_evidence(repo, package, source, f"result-{label}")
            evidence_path = next(package.glob(f"evidence/reconciliation-*-result-{label}.md"))
            evidence_path.write_text(
                mutate_result(evidence_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
            result_check = check_guard(token)
            assert result_check["outcome"] == INVALID
            assert any("single exact structural field" in error for error in result_check["errors"])

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        token = str(start_guard(context, repo)["token"])
        write_fresh_evidence(repo, package, source, "head-move")
        moved = git(repo, "commit", "--allow-empty", "-qm", "move head during reconciliation")
        assert moved.returncode == 0
        head_check = check_guard(token)
        assert head_check["outcome"] == INVALID
        assert any("HEAD/commit identity changed" in error for error in head_check["errors"])

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        token = str(start_guard(context, repo)["token"])
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["status"] = "planned"; meta_path.write_text(json.dumps(meta), encoding="utf-8")
        write_fresh_evidence(repo, package, source, "backward-state")
        backward = check_guard(token)
        assert backward["outcome"] == INVALID
        assert any("must remain implementing" in error for error in backward["errors"])

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); validator, adapter, package, source = write_fixture(repo, "iOS")
        other_source = repo / "iOS/Sources/Other.swift"; other_source.write_text("other baseline\n", encoding="utf-8")
        unrelated_task = (package / "plan/task-001.md").read_text(encoding="utf-8")
        unrelated_task = unrelated_task.replace("task-001 — Reconcile sample", "task-002 — Unrelated task")
        unrelated_task = unrelated_task.replace("evidence/task-001.md", "evidence/task-002.md")
        unrelated_task = unrelated_task.replace(source.relative_to(repo).as_posix(), other_source.relative_to(repo).as_posix())
        task_two = package / "plan/task-002.md"; task_two.write_text(unrelated_task, encoding="utf-8")
        (package / "evidence/task-002.md").write_text("Historical unrelated evidence.\n", encoding="utf-8")
        plan_readme = package / "plan/README.md"
        plan_readme.write_text(
            plan_readme.read_text(encoding="utf-8").replace(
                "task-001 is independent.", "task-001 and task-002 are independent."
            ),
            encoding="utf-8",
        )
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(tasks_total=2, tasks_done=2); meta_path.write_text(json.dumps(meta), encoding="utf-8")
        assert validator.validate_package(repo, adapter, "sample", "sample", "implement") == []
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "task-drift")
        token = str(start_guard(context, repo)["token"])
        task_two.write_text(
            re.sub(
                r"(?m)^- Status: .+$", "- Status: pending",
                task_two.read_text(encoding="utf-8"),
            ).replace("- Evidence: evidence/task-002.md", "- Evidence: none"),
            encoding="utf-8",
        )
        meta["tasks_done"] = 1; meta_path.write_text(json.dumps(meta), encoding="utf-8")
        plan_readme.write_text(
            plan_readme.read_text(encoding="utf-8")
            + "\n## Reconciliation bookkeeping\ntask-002 remains pending.\n",
            encoding="utf-8",
        )
        write_fresh_evidence(repo, package, source, "unrelated-task")
        unrelated_check = check_guard(token)
        assert unrelated_check["outcome"] == INVALID
        assert any("task file changes escape" in error for error in unrelated_check["errors"])

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "Android")
        context = resolve_context(repo, "android", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        token = str(start_guard(context, repo)["token"])
        write_fresh_evidence(repo, package, source, "android-aligned")
        narrative = next(package.glob("evidence/reconciliation-*-android-aligned.md"))
        narrative.write_text(
            narrative.read_text(encoding="utf-8")
            + "Narrative note: the focused result remains independently inspectable.\n",
            encoding="utf-8",
        )
        android_aligned = check_guard(token)
        assert android_aligned["outcome"] == RECONCILED, android_aligned

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "Android")
        context = resolve_context(repo, "android", "sample", "sample", [source.relative_to(repo).as_posix()], "platform-implementation-drift")
        started = start_guard(context, repo); token = str(started["token"])
        spec_path = package / "implementation-spec.md"
        spec_path.write_text(spec_path.read_text(encoding="utf-8").replace(
            "## Open questions", "Platform requirement reconciliation detail.\n\n## Open questions"
        ), encoding="utf-8")
        for name, addition in (
            ("design.md", "\nPlatform design reconciliation detail.\n"),
            ("verification.md", "\nPlatform verification reconciliation detail.\n"),
        ):
            path = package / name; path.write_text(path.read_text(encoding="utf-8") + addition, encoding="utf-8")
        task = package / "plan/task-001.md"
        task.write_text(task.read_text(encoding="utf-8").replace(
            "Keep the typed boundary aligned with platform contracts.",
            "Reconcile the typed boundary with the current platform requirement.",
        ), encoding="utf-8")
        write_fresh_evidence(repo, package, source, "platform-drift")
        checked = check_guard(token)
        assert checked["outcome"] == RECONCILED, checked

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(status="verified", verification_status="PASS", verified_at="2026-07-15T11:00:00Z", verification_state="evidence/verification-state.json")
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        verification = package / "verification.md"
        verification.write_text(verification.read_text(encoding="utf-8").replace("pending", "PASS"), encoding="utf-8")
        (package / "evidence/verification-state.json").write_text("{}\n", encoding="utf-8")
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        token = str(start_guard(context, repo)["token"])
        meta.update(status="implementing", verification_status="pending", verified_at=None, verification_state=None, problems=[])
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        verification.write_text(verification.read_text(encoding="utf-8").replace("PASS", "pending"), encoding="utf-8")
        write_fresh_evidence(repo, package, source, "verified-reset")
        checked = check_guard(token)
        assert checked["outcome"] == RECONCILED, checked

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "Android")
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(verification_status="FAIL", problems=["TST-AC-1"])
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        verification = package / "verification.md"
        verification.write_text(verification.read_text(encoding="utf-8").replace("pending", "FAIL", 1), encoding="utf-8")
        before = repository_snapshot(repo)
        context = resolve_context(repo, "android", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        assert context["outcome"] == ROUTE_REQUIRED
        assert "$implement" in str(context["route"])
        assert repository_snapshot(repo) == before

        bypass_context = resolve_context(repo, "android", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        bypass_context.update(
            outcome=ALIGNED,
            classification="aligned",
            platform_input="android",
            feature="sample",
            change="sample",
            package=package.relative_to(repo).as_posix(),
            intended_paths=[source.relative_to(repo).as_posix()],
            path_status={source.relative_to(repo).as_posix(): worktree_changes(repo)[source.relative_to(repo).as_posix()]},
            affected_task_closure=["task-001"],
            _package_path=package,
            _meta=meta.copy(),
            _adapter=_adapter,
        )
        token = str(start_guard(bypass_context, repo)["token"])
        meta["verification_status"] = "pending"; meta["problems"] = []
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        assert check_guard(token)["outcome"] == INVALID

    for field, value in (
        ("product_approval", "rewritten approval"),
        ("shared_product_spec", "specs/product/other/spec.md"),
        ("change_type", "rewritten-intake"),
    ):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
            context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
            token = str(start_guard(context, repo)["token"])
            meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta[field] = value; meta_path.write_text(json.dumps(meta), encoding="utf-8")
            write_fresh_evidence(repo, package, source, f"meta-{field}")
            protected = check_guard(token)
            assert protected["outcome"] == INVALID
            assert any(field in error and "protected meta authority" in error for error in protected["errors"])

    for early_status, expected_route in (("draft", "Propose"), ("specified", "Plan")):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
            meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["status"] = early_status; meta_path.write_text(json.dumps(meta), encoding="utf-8")
            before = repository_snapshot(repo)
            routed = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
            assert routed["outcome"] == ROUTE_REQUIRED and expected_route in str(routed["route"])
            assert repository_snapshot(repo) == before

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        meta_path = package / "meta.json"; meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.update(status="planned", tasks_done=0); meta_path.write_text(json.dumps(meta), encoding="utf-8")
        task_path = package / "plan/task-001.md"
        task_path.write_text(
            re.sub(r"(?m)^- Status: .+$", "- Status: pending", task_path.read_text(encoding="utf-8")).replace(
                "- Evidence: evidence/task-001.md", "- Evidence: none"
            ),
            encoding="utf-8",
        )
        context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        token = str(start_guard(context, repo)["token"])
        meta["status"] = "implementing"; meta["tasks_done"] = 1
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        task_path.write_text(
            re.sub(r"(?m)^- Status: .+$", "- Status: done", task_path.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        write_fresh_evidence(repo, package, source, "planned-transition")
        planned_checked = check_guard(token)
        assert planned_checked["outcome"] == RECONCILED, planned_checked

    for target in ("production", "historical-evidence", "shared-contract", "rule-authority", "unrelated"):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve(); _validator, adapter, package, source = write_fixture(repo, "iOS")
            context = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
            token = str(start_guard(context, repo)["token"])
            if target == "production": source.write_text("malicious second production edit\n", encoding="utf-8")
            elif target == "historical-evidence": (package / "evidence/task-001.md").write_text("rewritten\n", encoding="utf-8")
            elif target == "shared-contract": (repo / "specs/product/sample/spec.md").write_text("rewritten\n", encoding="utf-8")
            elif target == "rule-authority": (repo / "iOS/workflow/base.md").write_text("rewritten\n", encoding="utf-8")
            else: (repo / "unrelated.md").write_text("new unrelated write\n", encoding="utf-8")
            assert check_guard(token)["outcome"] == INVALID, target

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        archived_meta = json.loads((package / "meta.json").read_text(encoding="utf-8")); archived_meta["status"] = "archived"
        (package / "meta.json").write_text(json.dumps(archived_meta), encoding="utf-8")
        before = repository_snapshot(repo)
        archived = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "aligned")
        assert archived["outcome"] == ROUTE_REQUIRED and repository_snapshot(repo) == before
        other = package.parent / "other"; other.mkdir(); (other / "meta.json").write_text("{}\n", encoding="utf-8")
        ambiguous = resolve_context(repo, "ios", "sample", None, [source.relative_to(repo).as_posix()], "aligned")
        assert ambiguous["outcome"] == ROUTE_REQUIRED

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); _validator, _adapter, package, source = write_fixture(repo, "iOS")
        git(repo, "reset", "-q", "--hard", "HEAD")
        copied = source.with_name("Copied.swift"); copied.write_bytes(source.read_bytes())
        copy_context = resolve_context(
            repo, "ios", "sample", "sample", [copied.relative_to(repo).as_posix()], "task-drift"
        )
        assert copy_context["outcome"] == DRIFT
        assert copy_context["intended_paths"] == [copied.relative_to(repo).as_posix()]
        copied.unlink()
        original = source; renamed = source.with_name("Renamed.swift"); original.rename(renamed)
        one_side = resolve_context(repo, "ios", "sample", "sample", [renamed.relative_to(repo).as_posix()], "task-drift")
        assert one_side["outcome"] == ROUTE_REQUIRED
        both = resolve_context(repo, "ios", "sample", "sample", [original.relative_to(repo).as_posix(), renamed.relative_to(repo).as_posix()], "task-drift")
        assert both["outcome"] == DRIFT
        git(repo, "reset", "-q", "--hard", "HEAD")
        renamed.unlink()
        source.unlink()
        deleted = resolve_context(repo, "ios", "sample", "sample", [source.relative_to(repo).as_posix()], "task-drift")
        assert deleted["outcome"] == DRIFT

    print("reconcile-implementation self-test: PASS (drift, routes, guard, recovery, platforms, copy/rename/delete)")
    return 0


def add_identity(parser: argparse.ArgumentParser, *, classification: bool = True) -> None:
    parser.add_argument("--platform", required=True)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--change")
    parser.add_argument("--path", action="append", required=True, dest="paths")
    if classification:
        parser.add_argument("--classification", choices=sorted(CLASSIFICATIONS), default="auto")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    inspect_parser = subparsers.add_parser("inspect"); add_identity(inspect_parser)
    start_parser = subparsers.add_parser("start"); add_identity(start_parser)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("token"); check_parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.command == "check":
        report = check_guard(args.token); emit(report, args.as_json)
        return 0 if report.get("outcome") == RECONCILED else 2
    if args.command not in {"inspect", "start"}:
        parser.error("inspect, start, check or --self-test is required")
    try:
        repo = repository_root(args.root)
        context = resolve_context(
            repo, args.platform, args.feature, args.change, args.paths, args.classification
        )
        report = start_guard(context, repo) if args.command == "start" else public_report(context)
    except (OSError, ReconcileError, json.JSONDecodeError) as error:
        report = {"outcome": ROUTE_REQUIRED, "errors": [str(error)]}
    emit(report, args.as_json)
    return 2 if report.get("outcome") == ROUTE_REQUIRED else 0


if __name__ == "__main__":
    sys.exit(main())
