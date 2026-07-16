#!/usr/bin/env python3
"""Baseline/check guard for one implementation task's mutable scope."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import platform_path_ownership as path_ownership

BASELINE_SCHEMA_VERSION = 3
SNAPSHOT_ALGORITHM = "git-visible-lane-v1"
INDEX_ALGORITHM = "git-ls-files-stage-lane-v1"


def load_validator():
    path = Path(__file__).with_name("validate-platform-change.py")
    spec = importlib.util.spec_from_file_location("scope_platform_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load platform validator")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_tree(repo: Path, roots: list[str]) -> dict[str, str]:
    """Fingerprint Git-visible files only inside one explicit lane projection."""
    result: dict[str, str] = {}
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repo, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("git-visible snapshot requires a readable Git index")
    for payload in completed.stdout.split(b"\0"):
        if not payload:
            continue
        raw = payload.decode("utf-8", errors="surrogateescape")
        if not path_under(raw, roots):
            continue
        path = repo / raw
        if path.is_file():
            result[Path(raw).as_posix()] = hash_file(path)
    return result


def git_status(repo: Path, roots: list[str]) -> dict[str, str]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repo, text=True, capture_output=True, check=False,
    ).stdout
    result: dict[str, str] = {}
    entries = raw.split("\0"); index = 0
    while index < len(entries):
        entry = entries[index]; index += 1
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        if path_under(path, roots):
            result[path] = status
        if "R" in status or "C" in status:
            if index < len(entries):
                peer = entries[index]; index += 1
                if path_under(peer, roots):
                    result[peer] = status
    return result


def git_index_entries(repo: Path, roots: list[str]) -> dict[str, list[dict[str, str]]]:
    completed = subprocess.run(
        ["git", "ls-files", "--stage", "-z"], cwd=repo,
        capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("exact Git index snapshot requires a readable index")
    result: dict[str, list[dict[str, str]]] = {}
    for payload in completed.stdout.split(b"\0"):
        if not payload:
            continue
        metadata, separator, raw_path = payload.partition(b"\t")
        parts = metadata.decode("ascii", errors="strict").split()
        if not separator or len(parts) != 3:
            raise RuntimeError("git ls-files --stage returned malformed index entry")
        mode, blob_id, stage = parts
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if not path_under(path, roots):
            continue
        result.setdefault(Path(path).as_posix(), []).append({
            "mode": mode, "stage": stage, "blob_id": blob_id,
        })
    for entries in result.values():
        entries.sort(key=lambda item: (item["stage"], item["mode"], item["blob_id"]))
    return dict(sorted(result.items()))


def seal_error(target: Path, expected_sha256: str, label: str) -> str | None:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        return f"{label} expected SHA-256 token is invalid"
    if hash_file(target) != expected_sha256:
        return f"{label} integrity token mismatch"
    return None


def path_under(raw: str, roots: list[str]) -> bool:
    path = Path(raw)
    for root in roots:
        root_path = Path(root)
        if path == root_path or root_path in path.parents:
            return True
    return False


def path_overlaps(raw: str, roots: list[str]) -> bool:
    path = Path(raw)
    for root in roots:
        root_path = Path(root)
        if path == root_path or root_path in path.parents or path in root_path.parents:
            return True
    return False


def lane_control_roots(adapter: dict[str, object]) -> list[str]:
    platform_root = str(adapter["platform_root"]).rstrip("/")
    values = [
        "AGENTS.md", "workflow", ".agents/skills/implement", ".agents/skills/verify",
        f"{platform_root}/AGENTS.md", f"{platform_root}/workflow",
        str(adapter.get("_path", "")),
    ]
    return sorted(set(value for value in values if value))


def package_dependencies(
    repo: Path, adapter: dict[str, object], package: Path, meta: dict[str, object],
) -> list[str]:
    values = [package.relative_to(repo).as_posix(), *lane_control_roots(adapter)]
    shared = meta.get("shared_product_spec")
    if isinstance(shared, str):
        values.append(shared)
    for raw in meta.get("applicable_rule_files", []):
        if isinstance(raw, str):
            values.append(raw)
    return sorted(set(values))


def task_lane_projection(
    repo: Path, adapter: dict[str, object], package: Path, task_id: str,
    allowed: list[dict[str, str]],
) -> tuple[dict[str, list[str]], list[str]]:
    validator = load_validator()
    tasks, errors = validator.parse_tasks(repo, package, adapter=adapter)
    selected = next((task for task in tasks if task["id"] == task_id), None)
    if selected is None:
        return {}, errors + [f"task does not exist: {task_id}"]
    try:
        meta = json.loads((package / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, errors + ["meta.json is unavailable for lane projection"]
    mutable = sorted(set(str(item["path"]) for item in allowed))
    immutable = package_dependencies(repo, adapter, package, meta)
    immutable.extend(str(item) for item in selected.get("read_only_context", []))
    return {
        "mutable": mutable,
        "immutable": sorted(set(immutable)),
        "watched": sorted(set(mutable + immutable)),
    }, errors


def verify_lane_projection(
    repo: Path, adapter: dict[str, object], package: Path,
    tasks: list[dict[str, object]], meta: dict[str, object],
) -> dict[str, list[str]]:
    package_rel = package.relative_to(repo).as_posix()
    mutable = [
        f"{package_rel}/verification.md", f"{package_rel}/meta.json",
        f"{package_rel}/evidence",
    ]
    realized = [
        str(raw) for task in tasks for _kind, raw in task.get("paths", [])
    ]
    read_only = [
        str(raw) for task in tasks for raw in task.get("read_only_context", [])
    ]
    immutable = package_dependencies(repo, adapter, package, meta) + realized + read_only
    return {
        "mutable": sorted(set(mutable)),
        "immutable": sorted(set(immutable)),
        "watched": sorted(set(mutable + immutable)),
    }


def task_scope(repo: Path, adapter: dict[str, object], package: Path, task_id: str) -> tuple[list[dict[str, str]], list[str]]:
    validator = load_validator()
    tasks, errors = validator.parse_tasks(repo, package, adapter=adapter)
    selected = next((task for task in tasks if task["id"] == task_id), None)
    if selected is None:
        return [], errors + [f"task does not exist: {task_id}"]
    if selected["status"] != "pending":
        errors.append(f"task must be pending: {task_id}")
    by_id = {str(task["id"]): task for task in tasks}
    for dep in selected["deps"]:
        if by_id[str(dep)]["status"] != "done":
            errors.append(f"dependency is not done: {dep}")
    allowed: list[dict[str, str]] = []
    writable_paths: list[str] = []
    for _kind, raw in selected["paths"]:
        try:
            normalized = path_ownership.validate_platform_writable_path(
                repo, adapter, raw, require_existing=_kind == "existing"
            )
        except path_ownership.PathOwnershipError as error:
            errors.append(f"task Path ownership invalid: {error}")
            continue
        current = repo / normalized
        boundary = "dir" if current.is_dir() or (not current.exists() and not Path(normalized).suffix) else "file"
        allowed.append({"path": normalized.rstrip("/"), "boundary": boundary})
        writable_paths.append(normalized.rstrip("/"))
    if not allowed:
        errors.append("task has no writable Paths inside adapter production roots")
    owners = validator.active_task_path_owners(repo, adapter, writable_paths)
    package_rel = package.relative_to(repo).as_posix()
    for raw, package_owners in owners.items():
        foreign = [owner for owner in package_owners if owner != package_rel]
        if foreign:
            errors.append(
                f"task Path has ambiguous active package ownership: {raw}: "
                + ", ".join([package_rel, *foreign])
            )
    allowed.extend([
        {"path": f"{package_rel}/meta.json", "boundary": "file", "protected_exception": "true"},
        {"path": f"{package_rel}/plan/{task_id}.md", "boundary": "file", "protected_exception": "true"},
        {"path": f"{package_rel}/evidence/{task_id}.md", "boundary": "file", "protected_exception": "true"},
        {"path": f"{package_rel}/evidence/scope-baseline-{task_id}.json", "boundary": "file", "protected_exception": "true"},
    ])
    try:
        meta = json.loads((package / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        meta = {}
    if meta.get("verification_status") in {"FAIL", "UNKNOWN"}:
        allowed.append({"path": f"{package_rel}/verification.md", "boundary": "file", "protected_exception": "true"})
    return allowed, errors


def is_allowed(path: str, boundaries: list[dict[str, str]]) -> bool:
    value = Path(path)
    for boundary in boundaries:
        root = Path(boundary["path"])
        if boundary["boundary"] == "file" and value == root:
            return True
        if boundary["boundary"] == "dir" and (value == root or root in value.parents):
            return True
    return False


def is_explicit_protected_exception(path: str, boundaries: list[dict[str, str]]) -> bool:
    return any(
        boundary.get("protected_exception") == "true"
        and boundary.get("boundary") == "file"
        and Path(path) == Path(boundary["path"])
        for boundary in boundaries
    )


def create_baseline(repo: Path, platform: str, feature: str, change: str | None, task: str, target: Path) -> list[str]:
    validator = load_validator()
    adapter = validator.load_adapter(repo, platform)
    validator.require_capability(adapter, "implement")
    change_id, package = validator.resolve_change(repo, adapter, feature, change, "implement")
    package_errors = validator.validate_package(repo, adapter, feature, change_id, "implement")
    allowed, scope_errors = task_scope(repo, adapter, package, task)
    projection, projection_errors = task_lane_projection(repo, adapter, package, task, allowed)
    errors = package_errors + scope_errors + projection_errors
    expected_target = (package / "evidence" / f"scope-baseline-{task}.json").resolve()
    if target.resolve() != expected_target:
        errors.append(f"baseline must be exactly {expected_target.relative_to(repo)}")
    if errors:
        return errors
    data = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "snapshot_algorithm": SNAPSHOT_ALGORITHM,
        "index_algorithm": INDEX_ALGORITHM,
        "platform": platform, "feature": feature, "change_id": change_id, "task": task,
        "lane_identity": f"platform:{platform}:{feature}:{change_id}:task:{task}",
        "lane_projection": projection,
        "preexisting_status": git_status(repo, projection["watched"]),
        "index_entries": git_index_entries(repo, projection["watched"]),
        "files": snapshot_tree(repo, projection["watched"]), "allowed": allowed,
        "denied": sorted(set(str(x) for x in adapter["protected_roots"] + adapter["production_exclusions"])),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []


def check_baseline(repo: Path, target: Path, expected_sha256: str) -> list[str]:
    if not target.is_file():
        return ["baseline file is missing"]
    integrity_error = seal_error(target, expected_sha256, "baseline")
    if integrity_error:
        return [integrity_error]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["baseline JSON is invalid"]
    if (
        data.get("schema_version") != BASELINE_SCHEMA_VERSION
        or data.get("snapshot_algorithm") != SNAPSHOT_ALGORITHM
        or data.get("index_algorithm") != INDEX_ALGORITHM
    ):
        return ["baseline schema/snapshot algorithm marker is missing or stale"]
    validator = load_validator()
    try:
        adapter = validator.load_adapter(repo, str(data.get("platform", "")))
        validator.require_capability(adapter, "implement")
        _change_id, package = validator.resolve_change(
            repo, adapter, str(data.get("feature", "")),
            str(data.get("change_id", "")), "implement",
        )
    except (ValueError, OSError) as error:
        return [f"baseline identity is invalid: {error}"]
    expected_target = (package / "evidence" / f"scope-baseline-{data.get('task', '')}.json").resolve()
    if target.resolve() != expected_target:
        return [f"baseline must be exactly {expected_target.relative_to(repo)}"]
    projection = data.get("lane_projection", {})
    watched = projection.get("watched", []) if isinstance(projection, dict) else []
    if not isinstance(watched, list) or not watched:
        return ["baseline lane projection is missing or invalid"]
    before: dict[str, str] = data.get("files", {})
    after = snapshot_tree(repo, watched)
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    allowed = data.get("allowed", [])
    denied = data.get("denied", [])
    violations = sorted(
        path for path in changed
        if (path_under(path, denied) and not is_explicit_protected_exception(path, allowed))
        or not is_allowed(path, allowed)
    )
    before_status: dict[str, str] = data.get("preexisting_status", {})
    after_status = git_status(repo, watched)
    status_paths = set(before_status) | set(after_status)
    violations.extend(
        f"git-status:{path}" for path in sorted(status_paths)
        if before_status.get(path) != after_status.get(path) and not is_allowed(path, allowed)
    )
    before_index = data.get("index_entries")
    if not isinstance(before_index, dict):
        violations.append("git-index:<invalid-baseline>")
    else:
        after_index = git_index_entries(repo, watched)
        for path in sorted(set(before_index) | set(after_index)):
            if before_index.get(path) != after_index.get(path):
                violations.append(f"git-index:{path}")
    return [f"scope violation: {path}" for path in violations]


def create_verify_baseline(
    repo: Path, platform: str, feature: str, change: str | None, target: Path
) -> list[str]:
    validator = load_validator()
    adapter = validator.load_adapter(repo, platform)
    validator.require_capability(adapter, "verify")
    change_id, package = validator.resolve_change(repo, adapter, feature, change, "implement")
    errors = validator.validate_package(repo, adapter, feature, change_id, "implement")
    tasks, task_errors = validator.parse_tasks(repo, package, adapter=adapter); errors.extend(task_errors)
    if not tasks or any(task["status"] != "done" for task in tasks):
        errors.append("verify baseline requires all tasks done")
    try:
        candidate_meta = json.loads((package / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        candidate_meta = {}
    if candidate_meta.get("problems") != [] or candidate_meta.get("verification_status") != "pending":
        errors.append("verify baseline requires clean pending verification state")
    expected = (package / "evidence/verify-scope-baseline.json").resolve()
    if target.resolve() != expected:
        errors.append(f"verify baseline must be exactly {expected.relative_to(repo)}")
    if errors:
        return errors
    meta = json.loads((package / "meta.json").read_text(encoding="utf-8"))
    projection = verify_lane_projection(repo, adapter, package, tasks, meta)
    data = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "snapshot_algorithm": SNAPSHOT_ALGORITHM,
        "index_algorithm": INDEX_ALGORITHM,
        "mode": "verify", "platform": platform, "feature": feature,
        "change_id": change_id,
        "lane_identity": f"platform:{platform}:{feature}:{change_id}:verify",
        "lane_projection": projection,
        "preexisting_status": git_status(repo, projection["watched"]),
        "index_entries": git_index_entries(repo, projection["watched"]),
        "files": snapshot_tree(repo, projection["watched"]), "meta": meta,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []


def check_verify_baseline(repo: Path, target: Path, expected_sha256: str) -> list[str]:
    if not target.is_file():
        return ["verify baseline file is missing"]
    integrity_error = seal_error(target, expected_sha256, "verify baseline")
    if integrity_error:
        return [integrity_error]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["verify baseline JSON is invalid"]
    if (
        data.get("schema_version") != BASELINE_SCHEMA_VERSION
        or data.get("snapshot_algorithm") != SNAPSHOT_ALGORITHM
        or data.get("index_algorithm") != INDEX_ALGORITHM
    ):
        return ["verify baseline schema/snapshot algorithm marker is missing or stale"]
    if data.get("mode") != "verify":
        return ["baseline is not a verify scope baseline"]
    validator = load_validator()
    try:
        adapter = validator.load_adapter(repo, str(data.get("platform", "")))
        validator.require_capability(adapter, "verify")
        _change_id, package = validator.resolve_change(
            repo, adapter, str(data.get("feature", "")), str(data.get("change_id", "")), "implement"
        )
    except (ValueError, OSError) as error:
        return [f"verify baseline identity is invalid: {error}"]
    expected = (package / "evidence/verify-scope-baseline.json").resolve()
    if target.resolve() != expected:
        return [f"verify baseline must be exactly {expected.relative_to(repo)}"]
    projection = data.get("lane_projection", {})
    watched = projection.get("watched", []) if isinstance(projection, dict) else []
    if not isinstance(watched, list) or not watched:
        return ["verify baseline lane projection is missing or invalid"]
    before: dict[str, str] = data.get("files", {})
    after = snapshot_tree(repo, watched)
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    package_rel = package.relative_to(repo).as_posix()
    baseline_rel = f"{package_rel}/evidence/verify-scope-baseline.json"
    meta_rel = f"{package_rel}/meta.json"
    verification_rel = f"{package_rel}/verification.md"
    state_rel = f"{package_rel}/evidence/verification-state.json"
    evidence_root = Path(f"{package_rel}/evidence")
    violations: list[str] = []
    for path in sorted(changed):
        value = Path(path)
        if path in {baseline_rel, verification_rel, state_rel}:
            continue
        if path == meta_rel:
            continue
        if evidence_root in value.parents and path not in before:
            continue
        violations.append(path)
    meta_path = package / "meta.json"
    try:
        current_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        violations.append(meta_rel)
    else:
        original_meta = data.get("meta", {})
        allowed_meta = {"status", "problems", "verification_status", "verified_at", "verification_state"}
        for key in set(original_meta) | set(current_meta):
            if original_meta.get(key) != current_meta.get(key) and key not in allowed_meta:
                violations.append(f"{meta_rel}#{key}")
    before_status: dict[str, str] = data.get("preexisting_status", {})
    after_status = git_status(repo, watched)
    allowed_status = {baseline_rel, verification_rel, state_rel, meta_rel}
    for path in set(before_status) | set(after_status):
        value = Path(path)
        if before_status.get(path) == after_status.get(path):
            continue
        if path in allowed_status or (evidence_root in value.parents and path not in before):
            continue
        violations.append(f"git-status:{path}")
    before_index = data.get("index_entries")
    if not isinstance(before_index, dict):
        violations.append("git-index:<invalid-baseline>")
    else:
        after_index = git_index_entries(repo, watched)
        for path in sorted(set(before_index) | set(after_index)):
            if before_index.get(path) != after_index.get(path):
                violations.append(f"git-index:{path}")
    return [f"verify scope violation: {path}" for path in sorted(set(violations))]


def self_test() -> int:
    validator = load_validator()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); adapter, package, meta = validator.write_fixture(repo)
        plan = package / "plan"; plan.mkdir()
        (plan / "README.md").write_text("# Plan\n\n## Planning frame\nOne bounded implementation task follows approved contracts.\n\n## Revalidated engineering scopes and exact rules\n- Engineering scopes: [\"application\"]\n- Applicable rule files: [\"TestClient/workflow/base.md\", \"TestClient/workflow/application.md\"]\n\n## DAG\ntask-001 is ready without dependencies.\n\n## Estimates and multipliers\nGreenfield uncertainty is included in the task range.\n\n## Verification strategy\nRun one focused behavior check and record evidence.\n")
        task = "# task-001\n- Layer: domain\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Sources/Sample.swift\n\n## Goal\nImplement the typed sample boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the result.\n\n## Implementation deliverables\n- Typed sample behavior boundary in `Sample.swift`.\n- Focused behavior test for the deterministic result.\n\n## Steps\nCreate the boundary with a focused behavior test.\n\n## Verification\nRun the deterministic boundary test.\n\n## Expected result\nThe focused behavior test passes.\n\n## Out of scope\nOther features and platform cleanup remain excluded.\n"
        task = task.replace("- Layer: domain\n", "- Layer: domain\n- Boundary owner: Sample capability boundary\n", 1)
        task = task.replace("- Paths:", "- Read-only context: none\n- Paths:", 1)
        (plan / "task-001.md").write_text(task)
        meta.update(status="planned", tasks_total=1, rule_selection_snapshot="plan/rule-selection.json")
        (plan / "rule-selection.json").write_text(json.dumps(validator.rule_selection_snapshot(meta)))
        (package / "meta.json").write_text(json.dumps(meta))
        (repo / "unrelated.txt").write_text("preexisting\n")
        (repo / ".gitignore").write_text("node_modules/\nbuild/\n", encoding="utf-8")
        ignored_node = repo / "node_modules/cache/index.js"; ignored_node.parent.mkdir(parents=True)
        ignored_node.write_text("ignored cache\n", encoding="utf-8")
        ignored_build = repo / "build/output.bin"; ignored_build.parent.mkdir(parents=True)
        ignored_build.write_bytes(b"ignored build")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "scope@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Scope Test"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
        baseline = package / "evidence/scope-baseline-task-001.json"
        protected_task = task.replace(
            "proposed: TestClient/Sources/Sample.swift",
            "proposed: TestClient/Sources/Sample.swift; existing: TestClient/specs/sample/changes/sample/meta.json",
        )
        (plan / "task-001.md").write_text(protected_task)
        protected_errors = create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline)
        assert any("protected/excluded" in error for error in protected_errors)
        ancestor_task = task.replace("proposed: TestClient/Sources/Sample.swift", "existing: TestClient")
        (plan / "task-001.md").write_text(ancestor_task)
        ancestor_errors = create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline)
        assert any("protected/excluded" in error for error in ancestor_errors)
        (plan / "task-001.md").write_text(task)
        traversal_errors = create_baseline(repo, "test-client", "sample", "sample", "task-001", repo.parent / "escape.json")
        assert any("baseline must be exactly" in error for error in traversal_errors)
        baseline_errors = create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline)
        assert baseline_errors == [], baseline_errors
        duplicate_package = repo / "TestClient/specs/other/changes/second"
        shutil.copytree(package, duplicate_package)
        duplicate_meta = json.loads((duplicate_package / "meta.json").read_text())
        duplicate_meta.update(feature="other", change_id="second", status="planned")
        (duplicate_package / "meta.json").write_text(json.dumps(duplicate_meta))
        ambiguous_errors = create_baseline(
            repo, "test-client", "sample", "sample", "task-001", baseline
        )
        assert any("ambiguous active package ownership" in error for error in ambiguous_errors)
        shutil.rmtree(repo / "TestClient/specs/other")
        assert create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline) == []
        baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
        assert baseline_data["schema_version"] == BASELINE_SCHEMA_VERSION
        assert baseline_data["snapshot_algorithm"] == SNAPSHOT_ALGORITHM
        assert baseline_data["index_algorithm"] == INDEX_ALGORITHM
        assert not any(path.startswith(("node_modules/", "build/")) for path in baseline_data["files"])
        baseline_sha = hash_file(baseline)
        source = repo / "TestClient/Sources/Sample.swift"; source.parent.mkdir(parents=True); source.write_text("struct Sample {}\n")
        assert check_baseline(repo, baseline, baseline_sha) == []
        disjoint_commit = repo / "disjoint-note.txt"; disjoint_commit.write_text("unrelated lane\n")
        subprocess.run(["git", "add", "disjoint-note.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "unrelated lane commit"], cwd=repo, check=True)
        assert check_baseline(repo, baseline, baseline_sha) == []
        shared = repo / "specs/product/sample/spec.md"; original_shared = shared.read_text()
        shared.write_text(original_shared + "\nSelected shared drift.\n")
        assert any("specs/product/sample/spec.md" in error for error in check_baseline(repo, baseline, baseline_sha))
        shared.write_text(original_shared)
        adapter_path = repo / str(adapter["_path"]); original_adapter = adapter_path.read_text()
        adapter_path.write_text(original_adapter + "\n")
        assert check_baseline(repo, baseline, baseline_sha)
        adapter_path.write_text(original_adapter)
        subprocess.run(["git", "add", "TestClient/Sources/Sample.swift"], cwd=repo, check=True)
        assert any("git-index:TestClient/Sources/Sample.swift" in error for error in check_baseline(repo, baseline, baseline_sha))
        subprocess.run(["git", "reset", "-q", "--", "TestClient/Sources/Sample.swift"], cwd=repo, check=True)
        verification = package / "verification.md"; initial_verification = verification.read_text()
        verification.write_text(initial_verification + "\nInitial implementation must not edit verification.\n")
        assert any("verification.md" in error for error in check_baseline(repo, baseline, baseline_sha))
        verification.write_text(initial_verification)
        task_evidence = package / "evidence/task-001.md"; task_evidence.write_text("Focused PASS.\n")
        assert check_baseline(repo, baseline, baseline_sha) == []
        arbitrary_evidence = package / "evidence/arbitrary.md"; arbitrary_evidence.write_text("Not allowed.\n")
        assert any("arbitrary.md" in error for error in check_baseline(repo, baseline, baseline_sha))
        arbitrary_evidence.unlink()
        protected_rule = repo / "TestClient/workflow/application.md"; original_rule = protected_rule.read_text()
        protected_rule.write_text("Mutated protected rule.\n")
        assert any("TestClient/workflow/application.md" in error for error in check_baseline(repo, baseline, baseline_sha))
        protected_rule.write_text(original_rule)
        (repo / "unrelated.txt").write_text("changed after baseline\n")
        assert check_baseline(repo, baseline, baseline_sha) == []
        original_baseline = baseline.read_bytes()
        forged = json.loads(original_baseline)
        forged["files"]["unrelated.txt"] = hash_file(repo / "unrelated.txt")
        forged["allowed"].append({"path": "unrelated.txt", "boundary": "file"})
        baseline.write_text(json.dumps(forged))
        assert any("integrity token mismatch" in error for error in check_baseline(repo, baseline, baseline_sha))
        baseline.write_bytes(original_baseline)
        (repo / "unrelated.txt").write_text("preexisting\n")
        assert check_baseline(repo, baseline, baseline_sha) == []
        (repo / "unrelated.txt").write_text("owner dirty before task baseline\n")
        assert create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline) == []
        baseline_sha = hash_file(baseline)
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        assert check_baseline(repo, baseline, baseline_sha) == []
        subprocess.run(["git", "reset", "-q", "--", "unrelated.txt"], cwd=repo, check=True)
        (repo / "unrelated.txt").write_text("preexisting\n")
        unrelated = repo / "unrelated.txt"
        unrelated.write_text("staged version one\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        unrelated.write_text("stable worktree bytes\n")
        assert create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline) == []
        baseline_sha = hash_file(baseline)
        watched = json.loads(baseline.read_text())["lane_projection"]["watched"]
        mm_status = git_status(repo, watched)
        mm_files = snapshot_tree(repo, watched)
        unrelated.write_text("staged version two\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        unrelated.write_text("stable worktree bytes\n")
        assert git_status(repo, watched) == mm_status
        assert snapshot_tree(repo, watched) == mm_files
        index_only_errors = check_baseline(repo, baseline, baseline_sha)
        assert index_only_errors == [], index_only_errors
        subprocess.run(["git", "reset", "-q", "--", "unrelated.txt"], cwd=repo, check=True)
        unrelated.write_text("preexisting\n")
        for name in ("req", "ac", "preq", "pac"):
            (package / f"evidence/{name}.md").write_text("Concrete verifier evidence.\n")
        failed_verification = (
            "# Verification\n\n" + validator.fixture_modularity_verification("PASS")
            + "\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | FAIL |\n"
        )
        verification.write_text(failed_verification)
        recovery = dict(meta); recovery.update(status="implementing", tasks_total=1, tasks_done=0, verification_status="FAIL", problems=["TST-AC-1"])
        (package / "meta.json").write_text(json.dumps(recovery))
        recovery_baseline_errors = create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline)
        assert recovery_baseline_errors == [], recovery_baseline_errors
        baseline_sha = hash_file(baseline)
        pending_verification = re.sub(r"\| (?:PASS|FAIL|UNKNOWN) \|", "| pending |", failed_verification)
        pending_verification = re.sub(
            r"(?m)^(- (?:Dependency graph|Public API and visibility|Module-level tests|Consumer integration and build|App-shell allowlist):) PASS$",
            r"\1 pending",
            pending_verification,
        )
        verification.write_text(pending_verification)
        assert check_baseline(repo, baseline, baseline_sha) == []
        done_task = task.replace("Status: pending", "Status: done").replace("Evidence: none", "Evidence: evidence/task-001.md").replace("proposed:", "existing:")
        (plan / "task-001.md").write_text(done_task)
        verify_ready = dict(meta); verify_ready.update(status="implementing", tasks_done=1, problems=[], verification_status="pending", verified_at=None, verification_state=None)
        (package / "meta.json").write_text(json.dumps(verify_ready))
        unrelated = repo / "unrelated.txt"; unrelated.write_text("owner dirty before verify\n")
        verify_baseline = package / "evidence/verify-scope-baseline.json"
        assert create_verify_baseline(repo, "test-client", "sample", "sample", verify_baseline) == []
        verify_sha = hash_file(verify_baseline)
        verifier_evidence = package / "evidence/verify-new.md"; verifier_evidence.write_text("Fresh verifier evidence.\n")
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
        verify_disjoint = repo / "verify-disjoint.txt"; verify_disjoint.write_text("outside verify lane\n")
        subprocess.run(["git", "add", "verify-disjoint.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "verify unrelated commit"], cwd=repo, check=True)
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
        source.write_text("struct Sample { let verifierMutation = true }\n")
        assert any("Sample.swift" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
        original_verify_baseline = verify_baseline.read_bytes()
        forged_verify = json.loads(original_verify_baseline)
        forged_verify["files"]["TestClient/Sources/Sample.swift"] = hash_file(source)
        forged_verify["meta"]["engineering_scopes"] = ["forged"]
        verify_baseline.write_text(json.dumps(forged_verify))
        assert any("integrity token mismatch" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
        verify_baseline.write_bytes(original_verify_baseline)
        source.write_text("struct Sample {}\n")
        original_task = (plan / "task-001.md").read_text(); (plan / "task-001.md").write_text(original_task + "\nVerifier mutation.\n")
        assert any("task-001.md" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
        (plan / "task-001.md").write_text(original_task)
        original_rule = protected_rule.read_text(); protected_rule.write_text("Verifier changed selected rule.\n")
        assert any("application.md" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
        protected_rule.write_text(original_rule)
        original_task_evidence = task_evidence.read_text(); task_evidence.write_text("Verifier overwrote task proof.\n")
        assert any("task-001.md" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
        task_evidence.write_text(original_task_evidence)
        candidate_meta = dict(verify_ready); candidate_meta.update(status="verified", verification_status="PASS", verified_at="2026-07-15T12:00:00Z", verification_state="evidence/verification-state.json")
        (package / "meta.json").write_text(json.dumps(candidate_meta))
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
        (package / "meta.json").write_text(json.dumps(verify_ready))
        unrelated.write_text("changed after verify baseline\n")
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
        unrelated.write_text("owner dirty before verify\n")
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
        unrelated.write_text("verify staged version one\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        unrelated.write_text("verify stable worktree bytes\n")
        assert create_verify_baseline(repo, "test-client", "sample", "sample", verify_baseline) == []
        verify_sha = hash_file(verify_baseline)
        verify_watched = json.loads(verify_baseline.read_text())["lane_projection"]["watched"]
        verify_mm_status = git_status(repo, verify_watched)
        verify_mm_files = snapshot_tree(repo, verify_watched)
        unrelated.write_text("verify staged version two\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        unrelated.write_text("verify stable worktree bytes\n")
        assert git_status(repo, verify_watched) == verify_mm_status
        assert snapshot_tree(repo, verify_watched) == verify_mm_files
        verify_index_errors = check_verify_baseline(repo, verify_baseline, verify_sha)
        assert verify_index_errors == [], verify_index_errors
        subprocess.run(["git", "reset", "-q", "--", "unrelated.txt"], cwd=repo, check=True)
        unrelated.write_text("owner dirty before verify\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
    print("validate-implementation-scope self-test: PASS (scoped task/verify lanes and selected drift)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", choices=("snapshot", "check", "verify-snapshot", "verify-check"))
    parser.add_argument("--platform"); parser.add_argument("--feature"); parser.add_argument("--change"); parser.add_argument("--task")
    parser.add_argument("--baseline", type=Path); parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--expected-sha256")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test: return self_test()
    if not args.action or not args.baseline: parser.error("action and --baseline are required")
    repo = args.root.resolve()
    if args.baseline.is_absolute() or ".." in args.baseline.parts:
        print("Implementation scope: INVALID\n- baseline must be a safe repo-relative canonical package path")
        return 2
    target = (repo / args.baseline).resolve()
    if not target.is_relative_to(repo):
        print("Implementation scope: INVALID\n- baseline escapes repository root")
        return 2
    try:
        if args.action == "snapshot":
            if not args.platform or not args.feature or not args.task: parser.error("snapshot requires --platform, --feature and --task")
            errors = create_baseline(repo, args.platform, args.feature, args.change, args.task, target)
        elif args.action == "verify-snapshot":
            if not args.platform or not args.feature: parser.error("verify-snapshot requires --platform and --feature")
            errors = create_verify_baseline(repo, args.platform, args.feature, args.change, target)
        elif args.action == "verify-check":
            if not args.expected_sha256: parser.error("verify-check requires --expected-sha256")
            errors = check_verify_baseline(repo, target, args.expected_sha256)
        else:
            if not args.expected_sha256: parser.error("check requires --expected-sha256")
            errors = check_baseline(repo, target, args.expected_sha256)
    except (ValueError, OSError) as error:
        errors = [str(error)]
    if errors:
        print("Implementation scope: INVALID")
        for error in errors: print(f"- {error}")
        return 2
    print(f"Implementation scope: VALID ({args.action})")
    if args.action in {"snapshot", "verify-snapshot"}:
        print(f"Baseline SHA-256: {hash_file(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
