#!/usr/bin/env python3
"""Baseline/check guard for one implementation task's mutable scope."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

BASE_EXCLUDED_WALK = {".git", "__pycache__"}


def load_validator():
    path = Path(__file__).with_name("validate-platform-change.py")
    spec = importlib.util.spec_from_file_location("scope_platform_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load platform validator")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_tree(repo: Path, adapter: dict[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    excluded = BASE_EXCLUDED_WALK | {str(item) for item in adapter.get("context_excluded_directories", [])}
    for base, dirs, files in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in excluded]
        for name in files:
            path = Path(base) / name
            result[path.relative_to(repo).as_posix()] = hash_file(path)
    return result


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def git_status(repo: Path) -> dict[str, str]:
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
        result[path] = status
        if "R" in status or "C" in status:
            index += 1
    return result


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


def task_scope(repo: Path, adapter: dict[str, object], package: Path, task_id: str) -> tuple[list[dict[str, str]], list[str]]:
    validator = load_validator()
    tasks, errors = validator.parse_tasks(repo, package)
    selected = next((task for task in tasks if task["id"] == task_id), None)
    if selected is None:
        return [], errors + [f"task does not exist: {task_id}"]
    if selected["status"] != "pending":
        errors.append(f"task must be pending: {task_id}")
    by_id = {str(task["id"]): task for task in tasks}
    for dep in selected["deps"]:
        if by_id[str(dep)]["status"] != "done":
            errors.append(f"dependency is not done: {dep}")
    production = [str(x) for x in adapter["production_roots"]]
    excluded = [str(x) for x in adapter["protected_roots"]] + [str(x) for x in adapter["production_exclusions"]]
    allowed: list[dict[str, str]] = []
    for _kind, raw in selected["paths"]:
        if not path_under(raw, production):
            errors.append(f"task Path is outside adapter production roots: {raw}")
            continue
        if path_overlaps(raw, excluded):
            errors.append(f"task Path overlaps protected/excluded root: {raw}")
            continue
        current = repo / raw
        boundary = "dir" if current.is_dir() or (not current.exists() and not Path(raw).suffix) else "file"
        allowed.append({"path": Path(raw).as_posix().rstrip("/"), "boundary": boundary})
    if not allowed:
        errors.append("task has no writable Paths inside adapter production roots")
    package_rel = package.relative_to(repo).as_posix()
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
    errors = package_errors + scope_errors
    expected_target = (package / "evidence" / f"scope-baseline-{task}.json").resolve()
    if target.resolve() != expected_target:
        errors.append(f"baseline must be exactly {expected_target.relative_to(repo)}")
    if errors:
        return errors
    data = {
        "platform": platform, "feature": feature, "change_id": change_id, "task": task,
        "head": git_output(repo, "rev-parse", "HEAD"),
        "preexisting_status": git_status(repo),
        "files": snapshot_tree(repo, adapter), "allowed": allowed,
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
    before: dict[str, str] = data.get("files", {})
    after = snapshot_tree(repo, adapter)
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    head = str(data.get("head", ""))
    if head:
        changed.update(filter(None, git_output(repo, "diff", "--name-only", f"{head}..HEAD", "--").splitlines()))
    allowed = data.get("allowed", [])
    denied = data.get("denied", [])
    violations = sorted(
        path for path in changed
        if (path_under(path, denied) and not is_explicit_protected_exception(path, allowed))
        or not is_allowed(path, allowed)
    )
    before_status: dict[str, str] = data.get("preexisting_status", {})
    after_status = git_status(repo)
    status_paths = set(before_status) | set(after_status)
    violations.extend(
        f"git-status:{path}" for path in sorted(status_paths)
        if before_status.get(path) != after_status.get(path) and not is_allowed(path, allowed)
    )
    return [f"scope violation: {path}" for path in violations]


def create_verify_baseline(
    repo: Path, platform: str, feature: str, change: str | None, target: Path
) -> list[str]:
    validator = load_validator()
    adapter = validator.load_adapter(repo, platform)
    validator.require_capability(adapter, "verify")
    change_id, package = validator.resolve_change(repo, adapter, feature, change, "implement")
    errors = validator.validate_package(repo, adapter, feature, change_id, "implement")
    tasks, task_errors = validator.parse_tasks(repo, package); errors.extend(task_errors)
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
    data = {
        "mode": "verify", "platform": platform, "feature": feature,
        "change_id": change_id, "head": git_output(repo, "rev-parse", "HEAD"),
        "preexisting_status": git_status(repo),
        "files": snapshot_tree(repo, adapter), "meta": meta,
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
    before: dict[str, str] = data.get("files", {})
    after = snapshot_tree(repo, adapter)
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    head = str(data.get("head", ""))
    if head:
        changed.update(filter(None, git_output(repo, "diff", "--name-only", f"{head}..HEAD", "--").splitlines()))
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
    after_status = git_status(repo)
    allowed_status = {baseline_rel, verification_rel, state_rel, meta_rel}
    for path in set(before_status) | set(after_status):
        value = Path(path)
        if before_status.get(path) == after_status.get(path):
            continue
        if path in allowed_status or (evidence_root in value.parents and path not in before):
            continue
        violations.append(f"git-status:{path}")
    return [f"verify scope violation: {path}" for path in sorted(set(violations))]


def self_test() -> int:
    validator = load_validator()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); adapter, package, meta = validator.write_fixture(repo)
        plan = package / "plan"; plan.mkdir()
        (plan / "README.md").write_text("# Plan\n\n## Planning frame\nOne bounded implementation task follows approved contracts.\n\n## Revalidated engineering scopes and exact rules\n- Engineering scopes: [\"application\"]\n- Applicable rule files: [\"TestClient/workflow/base.md\", \"TestClient/workflow/application.md\"]\n\n## DAG\ntask-001 is ready without dependencies.\n\n## Estimates and multipliers\nGreenfield uncertainty is included in the task range.\n\n## Verification strategy\nRun one focused behavior check and record evidence.\n")
        task = "# task-001\n- Layer: domain\n- Engineering scopes: [\"application\"]\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Sources/Sample.swift\n\n## Goal\nImplement the typed sample boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the result.\n\n## Steps\nCreate the boundary with a focused behavior test.\n\n## Verification\nRun the deterministic boundary test.\n\n## Expected result\nThe focused behavior test passes.\n\n## Out of scope\nOther features and platform cleanup remain excluded.\n"
        (plan / "task-001.md").write_text(task)
        meta.update(status="planned", tasks_total=1, rule_selection_snapshot="plan/rule-selection.json")
        (plan / "rule-selection.json").write_text(json.dumps(validator.rule_selection_snapshot(meta)))
        (package / "meta.json").write_text(json.dumps(meta))
        (repo / "unrelated.txt").write_text("preexisting\n")
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
        assert create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline) == []
        baseline_sha = hash_file(baseline)
        source = repo / "TestClient/Sources/Sample.swift"; source.parent.mkdir(parents=True); source.write_text("struct Sample {}\n")
        assert check_baseline(repo, baseline, baseline_sha) == []
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
        assert any("unrelated.txt" in error for error in check_baseline(repo, baseline, baseline_sha))
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
        assert any("git-status:unrelated.txt" in error for error in check_baseline(repo, baseline, baseline_sha))
        subprocess.run(["git", "reset", "-q", "--", "unrelated.txt"], cwd=repo, check=True)
        (repo / "unrelated.txt").write_text("preexisting\n")
        for name in ("req", "ac", "preq", "pac"):
            (package / f"evidence/{name}.md").write_text("Concrete verifier evidence.\n")
        failed_verification = "# Verification\n\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | FAIL |\n"
        verification.write_text(failed_verification)
        recovery = dict(meta); recovery.update(status="implementing", tasks_total=1, tasks_done=0, verification_status="FAIL", problems=["TST-AC-1"])
        (package / "meta.json").write_text(json.dumps(recovery))
        assert create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline) == []
        baseline_sha = hash_file(baseline)
        verification.write_text(re.sub(r"\| (?:PASS|FAIL|UNKNOWN) \|", "| pending |", failed_verification))
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
        assert any("unrelated.txt" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
        unrelated.write_text("owner dirty before verify\n")
        assert check_verify_baseline(repo, verify_baseline, verify_sha) == []
        subprocess.run(["git", "add", "unrelated.txt"], cwd=repo, check=True)
        assert any("git-status:unrelated.txt" in error for error in check_verify_baseline(repo, verify_baseline, verify_sha))
    print("validate-implementation-scope self-test: PASS (task/verify guards and dirty preservation)")
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
