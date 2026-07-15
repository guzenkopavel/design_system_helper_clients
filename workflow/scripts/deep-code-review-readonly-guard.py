#!/usr/bin/env python3
"""Machine-enforced pre/post mutation guard for read-only deep-code-review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Callable


MAX_FILES = 50_000
MAX_FILE_BYTES = 50_000_000
MAX_TOTAL_BYTES = 500_000_000
MAX_STATE_BYTES = 16_000_000
TOKEN_RE = re.compile(r"^[0-9a-f]{64}$")
STATE_VERSION = 1


class GuardError(ValueError):
    pass


def git(repo: Path, *args: str) -> bytes:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", *args], cwd=repo, env=environment, capture_output=True, check=False,
    )
    if completed.returncode:
        raise GuardError("Git snapshot command failed")
    return completed.stdout


def repository_root() -> Path:
    output = git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(os.fsdecode(output.strip())).resolve()


def state_directory() -> Path:
    path = Path(tempfile.gettempdir()) / f"deep-code-review-readonly-{os.getuid()}"
    try:
        path.mkdir(mode=0o700, exist_ok=True)
        metadata = path.lstat()
    except OSError as error:
        raise GuardError("private guard state directory is unavailable") from error
    if path.is_symlink() or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise GuardError("private guard state directory is unsafe")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        try:
            path.chmod(0o700)
            metadata = path.lstat()
        except OSError as error:
            raise GuardError("private guard state permissions cannot be restricted") from error
        if stat.S_IMODE(metadata.st_mode) & 0o077:
            raise GuardError("private guard state directory is not private")
    return path


def state_path(token: str) -> Path:
    if not TOKEN_RE.fullmatch(token):
        raise GuardError("invalid opaque guard token")
    return state_directory() / f"{token}.json"


def decode_path(raw: bytes) -> str:
    return os.fsdecode(raw)


def governed_paths(repo: Path) -> list[str]:
    output = git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    paths = sorted({decode_path(item) for item in output.split(b"\0") if item})
    for value in paths:
        pure = PurePosixPath(value)
        if pure.is_absolute() or ".." in pure.parts:
            raise GuardError("Git returned an unsafe governed path")
    return paths


def index_snapshot(repo: Path) -> dict[str, list[str]]:
    output = git(repo, "ls-files", "--stage", "-z")
    entries: dict[str, list[str]] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
        except ValueError as error:
            raise GuardError("Git index record is invalid") from error
        entries.setdefault(decode_path(raw_path), []).append(metadata.decode("ascii", errors="strict"))
    for values in entries.values():
        values.sort()
    return entries


def hash_regular(path: Path, expected: os.stat_result) -> str:
    digest = hashlib.sha256()
    read = 0
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow:
        raise GuardError("platform lacks no-follow file snapshot support")
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow)
        opened = os.fstat(descriptor)
        if (
            opened.st_dev, opened.st_ino, opened.st_mode, opened.st_size
        ) != (
            expected.st_dev, expected.st_ino, expected.st_mode, expected.st_size
        ):
            os.close(descriptor)
            raise GuardError("governed file changed before bounded read")
        with os.fdopen(descriptor, "rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                read += len(chunk)
                if read > expected.st_size or read > MAX_FILE_BYTES:
                    raise GuardError("governed file changed beyond bounded snapshot")
                digest.update(chunk)
    except OSError as error:
        raise GuardError("governed file cannot be read") from error
    if read != expected.st_size:
        raise GuardError("governed file changed during snapshot")
    return digest.hexdigest()


def snapshot(
    repo: Path, *, max_files: int = MAX_FILES, max_file_bytes: int = MAX_FILE_BYTES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> tuple[dict[str, object] | None, list[dict[str, str]]]:
    repo = repo.resolve()
    issues: list[dict[str, str]] = []
    try:
        paths = governed_paths(repo)
        index = index_snapshot(repo)
    except GuardError as error:
        return None, [{"category": "git-snapshot", "path": ".", "message": str(error)}]
    if len(paths) > max_files:
        return None, [{
            "category": "file-budget", "path": ".",
            "message": f"Governed worktree exceeds bounded file budget ({max_files}).",
        }]

    worktree: dict[str, dict[str, object]] = {}
    total = 0
    for relative in paths:
        path = repo / relative
        try:
            before = path.lstat()
        except FileNotFoundError:
            worktree[relative] = {"type": "missing"}
            continue
        except OSError:
            issues.append({
                "category": "stat-error", "path": relative,
                "message": "Governed path metadata is unavailable.",
            })
            continue
        if stat.S_ISLNK(before.st_mode):
            try:
                target = os.readlink(path)
            except OSError:
                issues.append({
                    "category": "symlink-read-error", "path": relative,
                    "message": "Governed symlink target metadata is unavailable.",
                })
                continue
            encoded = os.fsencode(target)
            worktree[relative] = {
                "type": "symlink", "size": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
            continue
        if not stat.S_ISREG(before.st_mode):
            issues.append({
                "category": "non-regular", "path": relative,
                "message": "Governed path is not a regular file or symlink.",
            })
            continue
        if before.st_size > max_file_bytes:
            issues.append({
                "category": "file-size-budget", "path": relative,
                "message": f"Governed file exceeds bounded per-file budget ({max_file_bytes} bytes).",
            })
            continue
        if total + before.st_size > max_total_bytes:
            issues.append({
                "category": "total-byte-budget", "path": ".",
                "message": f"Governed worktree exceeds bounded total budget ({max_total_bytes} bytes).",
            })
            break
        try:
            digest = hash_regular(path, before)
            after = path.lstat()
        except (GuardError, OSError) as error:
            issues.append({
                "category": "read-error", "path": relative,
                "message": str(error) if isinstance(error, GuardError) else "Governed file metadata changed.",
            })
            continue
        if (
            before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode
        ) != (
            after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode
        ):
            issues.append({
                "category": "snapshot-race", "path": relative,
                "message": "Governed file changed during snapshot.",
            })
            continue
        total += before.st_size
        worktree[relative] = {
            "type": "file", "size": before.st_size, "sha256": digest,
        }
    if issues:
        return None, issues
    try:
        final_paths = governed_paths(repo)
        final_index = index_snapshot(repo)
    except GuardError as error:
        return None, [{"category": "git-snapshot", "path": ".", "message": str(error)}]
    if final_paths != paths or final_index != index:
        return None, [{
            "category": "snapshot-race", "path": ".",
            "message": "Governed Git state changed during snapshot.",
        }]
    root_meta = repo.stat()
    git_dir = Path(os.fsdecode(git(repo, "rev-parse", "--absolute-git-dir").strip())).resolve()
    return {
        "version": STATE_VERSION,
        "root": str(repo),
        "root_device": root_meta.st_dev,
        "root_inode": root_meta.st_ino,
        "git_dir": str(git_dir),
        "index": index,
        "worktree": worktree,
    }, []


def write_state(state: dict[str, object]) -> str:
    directory = state_directory()
    for _ in range(8):
        token = secrets.token_hex(32)
        path = directory / f"{token}.json"
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(state, stream, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return token
    raise GuardError("cannot allocate opaque guard token")


def state_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def load_state(
    token: str, *, max_state_bytes: int = MAX_STATE_BYTES,
    _after_open: Callable[[], None] | None = None,
) -> tuple[Path, dict[str, object]]:
    path = state_path(token)
    try:
        metadata = path.lstat()
    except OSError as error:
        raise GuardError("guard token is unavailable") from error
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
        raise GuardError("guard token state is unsafe")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise GuardError("guard token state permissions are unsafe")
    if metadata.st_size > max_state_bytes:
        raise GuardError("guard token state exceeds bounded size")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow:
        raise GuardError("platform lacks no-follow token state support")
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or stat.S_IMODE(opened.st_mode) != 0o600
            or state_identity(opened) != state_identity(metadata)
        ):
            raise GuardError("guard token state identity changed before bounded read")
        if _after_open is not None:
            _after_open()
        chunks: list[bytes] = []
        total = 0
        while True:
            remaining = max_state_bytes + 1 - total
            if remaining <= 0:
                raise GuardError("guard token state exceeds bounded size")
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_state_bytes:
                raise GuardError("guard token state exceeds bounded size")
        opened_after = os.fstat(descriptor)
        if state_identity(opened_after) != state_identity(opened):
            raise GuardError("guard token state changed during bounded read")
    except OSError as error:
        raise GuardError("guard token state is invalid") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as error:
        raise GuardError("guard token state changed after bounded read") from error
    if state_identity(after) != state_identity(metadata):
        raise GuardError("guard token state identity changed after bounded read")
    try:
        payload = json.loads(b"".join(chunks).decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError("guard token state is invalid") from error
    if not isinstance(payload, dict) or payload.get("version") != STATE_VERSION:
        raise GuardError("guard token state schema is invalid")
    return path, payload


def validate_state_root(repo: Path, state: dict[str, object]) -> None:
    repo = repo.resolve()
    metadata = repo.stat()
    if (
        state.get("root") != str(repo)
        or state.get("root_device") != metadata.st_dev
        or state.get("root_inode") != metadata.st_ino
        or state.get("git_dir") != str(Path(os.fsdecode(git(repo, "rev-parse", "--absolute-git-dir").strip())).resolve())
    ):
        raise GuardError("guard token belongs to another repository identity")


def changed_paths(before: dict[str, object], after: dict[str, object]) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for area in ("index", "worktree"):
        old = before.get(area)
        new = after.get(area)
        if not isinstance(old, dict) or not isinstance(new, dict):
            raise GuardError("guard snapshot schema is invalid")
        for path in sorted(set(old) | set(new)):
            if path not in old:
                category = f"{area}-added"
            elif path not in new:
                category = f"{area}-removed"
            elif old[path] != new[path]:
                category = f"{area}-changed"
            else:
                continue
            changes.append({"category": category, "path": path})
    return changes


def start(repo: Path, **limits: int) -> tuple[dict[str, object], int]:
    state, issues = snapshot(repo, **limits)
    if issues or state is None:
        return {"status": "UNKNOWN", "token": None, "coverage_issues": issues}, 3
    token = write_state(state)
    return {"status": "PASS", "token": token, "coverage_issues": []}, 0


def check(repo: Path, token: str) -> tuple[dict[str, object], int]:
    path, before = load_state(token)
    try:
        validate_state_root(repo, before)
        after, issues = snapshot(repo)
        if issues or after is None:
            return {"status": "UNKNOWN", "changes": [], "coverage_issues": issues}, 3
        changes = changed_paths(before, after)
        if changes:
            return {"status": "INVALID", "changes": changes, "coverage_issues": []}, 2
        return {"status": "PASS", "changes": [], "coverage_issues": []}, 0
    finally:
        path.unlink(missing_ok=True)


def configure_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)


def commit_all(repo: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        clean = base / "clean"; configure_repo(clean)
        (clean / "tracked.txt").write_text("base", encoding="utf-8"); commit_all(clean)
        before_status = git(clean, "status", "--porcelain=v1", "-z")
        payload, code = start(clean); assert code == 0 and isinstance(payload["token"], str)
        checked, code = check(clean, str(payload["token"])); assert code == 0 and checked["status"] == "PASS"
        assert git(clean, "status", "--porcelain=v1", "-z") == before_status
        assert (clean / "tracked.txt").read_text(encoding="utf-8") == "base"

        dirty = base / "dirty"; configure_repo(dirty)
        target = dirty / "tracked.txt"; target.write_text("base", encoding="utf-8"); commit_all(dirty)
        target.write_text("dirty-one", encoding="utf-8")
        payload, code = start(dirty); assert code == 0
        target.write_text("dirty-two", encoding="utf-8")
        checked, code = check(dirty, str(payload["token"]))
        assert code == 2 and {item["category"] for item in checked["changes"]} >= {"worktree-changed"}
        assert target.read_text(encoding="utf-8") == "dirty-two"

        staged = base / "staged"; configure_repo(staged)
        target = staged / "tracked.txt"; target.write_text("base", encoding="utf-8"); commit_all(staged)
        payload, _ = start(staged)
        target.write_text("staged", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=staged, check=True)
        checked, code = check(staged, str(payload["token"]))
        assert code == 2 and "index-changed" in {item["category"] for item in checked["changes"]}
        assert git(staged, "diff", "--cached", "--name-only").strip() == b"tracked.txt"

        untracked = base / "untracked"; configure_repo(untracked)
        (untracked / "base.txt").write_text("base", encoding="utf-8"); commit_all(untracked)
        existing = untracked / "existing.txt"; existing.write_text("one", encoding="utf-8")
        payload, _ = start(untracked)
        existing.write_text("two", encoding="utf-8")
        (untracked / "added.txt").write_text("added", encoding="utf-8")
        checked, code = check(untracked, str(payload["token"]))
        categories = {item["category"] for item in checked["changes"]}
        assert code == 2 and {"worktree-changed", "worktree-added"} <= categories

        budget = base / "budget"; configure_repo(budget)
        (budget / "one.txt").write_text("one", encoding="utf-8")
        (budget / "two.txt").write_text("two", encoding="utf-8")
        payload, code = start(budget, max_files=1)
        assert code == 3 and payload["status"] == "UNKNOWN" and payload["token"] is None

        wrong = base / "wrong"; configure_repo(wrong)
        (wrong / "base.txt").write_text("base", encoding="utf-8"); commit_all(wrong)
        payload, _ = start(clean)
        wrong_token = str(payload["token"])
        try:
            check(wrong, wrong_token)
        except GuardError:
            pass
        else:
            raise AssertionError("wrong-repository token accepted")
        assert not state_path(wrong_token).exists()

        payload, _ = start(clean)
        oversized_token = str(payload["token"])
        oversized_path = state_path(oversized_token)
        oversized_path.write_bytes(b"x" * 32)
        oversized_path.chmod(0o600)
        try:
            load_state(oversized_token, max_state_bytes=16)
        except GuardError:
            pass
        else:
            raise AssertionError("oversized token state accepted")
        oversized_path.unlink(missing_ok=True)

        payload, _ = start(clean)
        replaced_token = str(payload["token"])
        replaced_path = state_path(replaced_token)
        replacement = replaced_path.with_suffix(".replacement")
        replacement.write_text("{}", encoding="utf-8")
        replacement.chmod(0o600)
        def replace_token() -> None:
            os.replace(replacement, replaced_path)
        try:
            load_state(replaced_token, _after_open=replace_token)
        except GuardError:
            pass
        else:
            raise AssertionError("replaced token state accepted")
        replaced_path.unlink(missing_ok=True)

        symlink_token = secrets.token_hex(32)
        symlink_path = state_path(symlink_token)
        outside_state = base / "outside-state.json"
        outside_state.write_text('{"secret":"must-not-be-read"}', encoding="utf-8")
        symlink_path.symlink_to(outside_state)
        try:
            load_state(symlink_token)
        except GuardError as error:
            assert "must-not-be-read" not in str(error)
        else:
            raise AssertionError("symlink token state accepted")
        symlink_path.unlink(missing_ok=True)

        try:
            check(clean, "../unsafe")
        except GuardError:
            pass
        else:
            raise AssertionError("unsafe token accepted")
    print("deep-code-review-readonly-guard self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--self-test", action="store_true")
    subcommands = cli.add_subparsers(dest="command")
    subcommands.add_parser("start")
    check_parser = subcommands.add_parser("check")
    check_parser.add_argument("token")
    args = cli.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        repo = repository_root()
        if args.command == "start":
            payload, code = start(repo)
        elif args.command == "check":
            payload, code = check(repo, args.token)
        else:
            raise GuardError("start or check command is required")
    except (GuardError, OSError) as error:
        payload, code = {"status": "INVALID", "error": str(error), "changes": []}, 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
