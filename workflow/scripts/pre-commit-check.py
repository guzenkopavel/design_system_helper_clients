#!/usr/bin/env python3
"""Staged-index pre-commit gate. Never stages, commits, pushes, or prints secrets."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from platform_rule_profiles import RuleProfileError, validate_pre_commit_profile


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


@dataclass(frozen=True)
class Entry:
    status: str
    path: str
    old_path: str | None = None


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=repo, input=input_bytes, capture_output=True, check=False
    )


def repository_root(start: Path | None = None) -> Path:
    result = git((start or Path.cwd()).resolve(), "rev-parse", "--show-toplevel")
    if result.returncode:
        raise ValueError("not inside a Git repository")
    return Path(result.stdout.decode().strip()).resolve()


def staged_entries(repo: Path) -> list[Entry]:
    raw = git(repo, "diff", "--cached", "--name-status", "-z", "--find-renames", "--find-copies-harder").stdout
    parts = raw.split(b"\0"); result: list[Entry] = []; index = 0
    while index < len(parts) and parts[index]:
        status = parts[index].decode("utf-8", errors="replace"); index += 1
        if status.startswith(("R", "C")):
            old_path = parts[index].decode("utf-8", errors="surrogateescape"); index += 1
            path = parts[index].decode("utf-8", errors="surrogateescape"); index += 1
            result.append(Entry(status[0], path, old_path))
        else:
            path = parts[index].decode("utf-8", errors="surrogateescape"); index += 1
            result.append(Entry(status[:1], path))
    return result


def staged_fingerprint(repo: Path) -> str:
    names = git(repo, "diff", "--cached", "--name-status", "-z", "--find-renames", "--find-copies-harder").stdout
    index = git(repo, "ls-files", "-s", "-z").stdout
    diff = git(repo, "diff", "--cached", "--binary", "--no-ext-diff").stdout
    return hashlib.sha256(names + b"\0INDEX\0" + index + b"\0DIFF\0" + diff).hexdigest()


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


def task_trail(
    repo: Path, adapter: dict[str, object], candidate: str, changed_paths: set[str]
) -> dict[str, object] | None:
    package_root = str(adapter["package_root"]).rstrip("/")
    meta_re = re.compile(
        rf"^{re.escape(package_root)}/[^/]+/{re.escape(str(adapter['active_changes_namespace']))}/[^/]+/meta\.json$"
    )
    paths = index_paths(repo)
    fallback: dict[str, object] | None = None
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
            if result["done"] and result["evidence"]:
                return result
            fallback = fallback or result
    return fallback


def worktree_task_trail(repo: Path, adapter: dict[str, object], candidate: str) -> dict[str, object] | None:
    package_root = repo / str(adapter["package_root"])
    if not package_root.is_dir():
        return None
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
                return {
                    "package": package.relative_to(repo).as_posix(),
                    "task": task_path.stem,
                    "scopes": parse_task_scopes(body),
                    "command": parse_task_command(body),
                }
    return None


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


def evaluate(repo: Path) -> dict[str, object]:
    before = staged_fingerprint(repo)
    entries = staged_entries(repo)
    checks: list[dict[str, str]] = []
    if not entries:
        add(checks, "staged.non-empty", FAIL, "no staged changes")
        return {"status": FAIL, "fingerprint": before, "checks": checks}
    add(checks, "staged.non-empty", PASS, f"{len(entries)} staged entries")

    if git(repo, "ls-files", "-u").stdout:
        add(checks, "staged.unmerged", FAIL, "unmerged index entries exist")
    else:
        add(checks, "staged.unmerged", PASS, "no unmerged index entries")
    if git(repo, "diff", "--cached", "--check").returncode:
        add(checks, "staged.diff-check", FAIL, "staged diff has whitespace/conflict errors")
    else:
        add(checks, "staged.diff-check", PASS, "staged diff check passed")

    adapters, adapter_errors = load_adapter_state(repo, from_index=True)
    changed_paths = {
        path for entry in entries for path in (entry.path, entry.old_path) if path
    }
    indexed_paths = set(index_paths(repo))
    production_seen = False
    harness_seen = False
    trails_by_platform: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        path = entry.path
        candidates = [path] + ([entry.old_path] if entry.old_path else [])
        harness_seen = harness_seen or any(
            candidate == prefix or candidate.startswith(prefix)
            for candidate in candidates for prefix in HARNESS_PREFIXES
        )
        adapter = adapter_for_production(path, adapters)
        profile = adapter["pre_commit"] if adapter else None
        generated = list(COMMON_GENERATED) + (list(profile["generated_globs"]) if profile else [])
        secrets = list(COMMON_SECRET_PATHS) + (list(profile["secret_globs"]) if profile else [])
        if entry.status != "D" and glob_match(path, generated):
            add(checks, "path.generated-local", FAIL, "generated/local artifact is staged", path)
        if entry.status != "D" and glob_match(path, secrets):
            add(checks, "path.secret-material", FAIL, "secret/key material path is staged", path)

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
            trail = task_trail(repo, candidate_adapter, candidate, changed_paths)
            if not trail:
                add(checks, "trail.production-task", FAIL, "production path is not covered by an active staged task", candidate)
                continue
            trails_by_platform.setdefault(str(candidate_adapter["platform_root"]), []).append(trail)
            if not (trail["done"] and trail["evidence"]):
                add(checks, "trail.production-task", UNKNOWN, f"{trail['task']} is pending or lacks staged evidence", candidate)
            else:
                add(checks, "trail.production-task", PASS, f"covered by completed {trail['task']} with staged evidence", candidate)
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
                if not discovered_tools or any(not trail["command"] or not trail["evidence"] for trail in trails):
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
        trail = worktree_task_trail(repo, adapter, path)
        profile = adapter["pre_commit"]
        scoped_surface = glob_match(path, list(profile["security_sensitive_globs"]) + list(profile["project_globs"]))
        valid = bool(trail) and (not scoped_surface or bool(trail["scopes"]))
        detail = (
            f"covered by {trail['task']}" if valid
            else "active task with engineering scopes is required" if trail and scoped_surface
            else "no active task covers path"
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


def fixture_adapter(platform: str) -> dict[str, object]:
    root = platform
    suffix = ".swift" if platform == "iOS" else ".kt"
    return {
        "platform_name": platform, "platform_root": root,
        "package_root": f"{root}/specs", "active_changes_namespace": "changes",
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
        git(repo, "reset", "-q", "--hard", "HEAD")
        write(repo / "unrelated.tmp", "untracked owner state\n")
        before_untracked = (repo / "unrelated.tmp").read_text()
        write(repo / "safe.md", "safe\n"); git(repo, "add", "safe.md"); assert evaluate(repo)["status"] == PASS
        assert (repo / "unrelated.tmp").read_text() == before_untracked
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
            write(repo / f"{platform}/App/{source}", "safe source\n")
            write(repo / f"{platform}/App/Project.config", "project fixture\n")
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
            git(repo, "reset", "-q", "HEAD", sibling.relative_to(repo).as_posix()); sibling.unlink()
            git(repo, "commit", "-qm", f"{platform.lower()} fixture")

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
            copy_entries = staged_entries(repo)
            assert any(entry.status == "C" and entry.old_path == orphan.relative_to(repo).as_posix() for entry in copy_entries)
            copied_report = evaluate(repo)
            assert copied_report["status"] == FAIL
            copy_paths = {item.get("path") for item in copied_report["checks"]}
            assert orphan.relative_to(repo).as_posix() in copy_paths
            assert copied.relative_to(repo).as_posix() in copy_paths
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
    print("pre-commit-check self-test: PASS (index-only, evidence/tools, adapter fail-closed, rename/copy/delete)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true")
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
        report = evaluate(repo)
    else:
        parser.error("--staged or --path-coverage is required")
    emit(report, args.as_json)
    return 0 if report["status"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
