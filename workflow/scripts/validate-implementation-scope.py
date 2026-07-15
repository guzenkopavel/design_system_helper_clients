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

EXCLUDED_WALK = {".git", ".build", ".gradle", "DerivedData", "build", "node_modules", "__pycache__"}


def load_validator():
    path = Path(__file__).with_name("validate-platform-change.py")
    spec = importlib.util.spec_from_file_location("scope_platform_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load platform validator")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_tree(repo: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for base, dirs, files in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in EXCLUDED_WALK]
        for name in files:
            path = Path(base) / name
            result[path.relative_to(repo).as_posix()] = hash_file(path)
    return result


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    return result.stdout.strip()


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
        "preexisting_status": git_output(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines(),
        "files": snapshot_tree(repo), "allowed": allowed,
        "denied": sorted(set(str(x) for x in adapter["protected_roots"] + adapter["production_exclusions"])),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return []


def check_baseline(repo: Path, target: Path) -> list[str]:
    if not target.is_file():
        return ["baseline file is missing"]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["baseline JSON is invalid"]
    validator = load_validator()
    try:
        adapter = validator.load_adapter(repo, str(data.get("platform", "")))
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
    after = snapshot_tree(repo)
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
    return [f"scope violation: {path}" for path in violations]


def self_test() -> int:
    validator = load_validator()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve(); adapter, package, meta = validator.write_fixture(repo)
        plan = package / "plan"; plan.mkdir()
        (plan / "README.md").write_text("# Plan\n\n## Planning frame\nOne bounded implementation task follows approved contracts.\n\n## DAG\ntask-001 is ready without dependencies.\n\n## Estimates and multipliers\nGreenfield uncertainty is included in the task range.\n\n## Verification strategy\nRun one focused behavior check and record evidence.\n")
        task = "# task-001\n- Layer: domain\n- Depends on: none\n- Status: pending\n- Evidence: none\n- Estimate (ideal): 0.5–1 days\n- Paths: proposed: TestClient/Sources/Sample.swift\n\n## Goal\nImplement the typed sample boundary.\n\n## Inline contract context\nTST-REQ-1 defines the boundary and TST-AC-1 observes the result.\n\n## Steps\nCreate the boundary with a focused behavior test.\n\n## Verification\nRun the deterministic boundary test.\n\n## Expected result\nThe focused behavior test passes.\n\n## Out of scope\nOther features and platform cleanup remain excluded.\n"
        (plan / "task-001.md").write_text(task)
        meta.update(status="planned", tasks_total=1)
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
        source = repo / "TestClient/Sources/Sample.swift"; source.parent.mkdir(parents=True); source.write_text("struct Sample {}\n")
        assert check_baseline(repo, baseline) == []
        verification = package / "verification.md"; initial_verification = verification.read_text()
        verification.write_text(initial_verification + "\nInitial implementation must not edit verification.\n")
        assert any("verification.md" in error for error in check_baseline(repo, baseline))
        verification.write_text(initial_verification)
        task_evidence = package / "evidence/task-001.md"; task_evidence.write_text("Focused PASS.\n")
        assert check_baseline(repo, baseline) == []
        arbitrary_evidence = package / "evidence/arbitrary.md"; arbitrary_evidence.write_text("Not allowed.\n")
        assert any("arbitrary.md" in error for error in check_baseline(repo, baseline))
        arbitrary_evidence.unlink()
        protected_rule = repo / "TestClient/workflow/rule.md"; original_rule = protected_rule.read_text()
        protected_rule.write_text("Mutated protected rule.\n")
        assert any("TestClient/workflow/rule.md" in error for error in check_baseline(repo, baseline))
        protected_rule.write_text(original_rule)
        (repo / "unrelated.txt").write_text("changed after baseline\n")
        assert any("unrelated.txt" in error for error in check_baseline(repo, baseline))
        (repo / "unrelated.txt").write_text("preexisting\n")
        assert check_baseline(repo, baseline) == []
        for name in ("req", "ac", "preq", "pac"):
            (package / f"evidence/{name}.md").write_text("Concrete verifier evidence.\n")
        failed_verification = "# Verification\n\n| Contract ID | Layer | Method | Expected evidence | Status |\n|---|---|---|---|---|\n| REQ-1 | contract | Review current shared requirement | evidence/req.md | PASS |\n| AC-1 | integration | Run shared scenario | evidence/ac.md | PASS |\n| TST-REQ-1 | design | Review current boundary | evidence/preq.md | PASS |\n| TST-AC-1 | unit | Run focused boundary test | evidence/pac.md | FAIL |\n"
        verification.write_text(failed_verification)
        recovery = dict(meta); recovery.update(status="implementing", tasks_total=1, tasks_done=0, verification_status="FAIL", problems=["TST-AC-1"])
        (package / "meta.json").write_text(json.dumps(recovery))
        assert create_baseline(repo, "test-client", "sample", "sample", "task-001", baseline) == []
        verification.write_text(re.sub(r"\| (?:PASS|FAIL|UNKNOWN) \|", "| pending |", failed_verification))
        assert check_baseline(repo, baseline) == []
    print("validate-implementation-scope self-test: PASS (ready deps, allowed paths, dirty preservation)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", choices=("snapshot", "check"))
    parser.add_argument("--platform"); parser.add_argument("--feature"); parser.add_argument("--change"); parser.add_argument("--task")
    parser.add_argument("--baseline", type=Path); parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
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
        else:
            errors = check_baseline(repo, target)
    except (ValueError, OSError) as error:
        errors = [str(error)]
    if errors:
        print("Implementation scope: INVALID")
        for error in errors: print(f"- {error}")
        return 2
    print(f"Implementation scope: VALID ({args.action})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
