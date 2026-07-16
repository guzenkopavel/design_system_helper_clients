#!/usr/bin/env python3
"""Canonical Git change entries and identity/mutable/read-only path sets."""

from __future__ import annotations

import argparse
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChangeEntry:
    status: str
    path: str
    old_path: str | None = None


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)


def parse_name_status(raw: bytes) -> list[ChangeEntry]:
    parts = raw.split(b"\0"); result: list[ChangeEntry] = []; index = 0
    while index < len(parts) and parts[index]:
        status = parts[index].decode("utf-8", errors="replace"); index += 1
        kind = status[:1]
        if kind in {"R", "C"}:
            source = parts[index].decode("utf-8", errors="surrogateescape"); index += 1
            destination = parts[index].decode("utf-8", errors="surrogateescape"); index += 1
            result.append(ChangeEntry(kind, destination, source))
        else:
            path = parts[index].decode("utf-8", errors="surrogateescape"); index += 1
            result.append(ChangeEntry(kind, path))
    return result


def staged_entries(repo: Path) -> list[ChangeEntry]:
    return parse_name_status(
        git(
            repo, "diff", "--cached", "--name-status", "-z",
            "--find-renames",
        ).stdout
    )


def head_blob_inventory(repo: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for payload in git(repo, "ls-tree", "-r", "-z", "HEAD").stdout.split(b"\0"):
        if not payload:
            continue
        metadata, separator, raw_path = payload.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3 or fields[1] != b"blob" or fields[0] == b"120000":
            continue
        path = raw_path.decode("utf-8", errors="surrogateescape")
        result.setdefault(fields[2].decode("ascii"), []).append(path)
    return result


def head_path_entry(repo: Path, raw: str) -> tuple[str, str] | None:
    payloads = [item for item in git(repo, "ls-tree", "-z", "HEAD", "--", raw).stdout.split(b"\0") if item]
    if len(payloads) != 1:
        return None
    metadata, separator, raw_path = payloads[0].partition(b"\t")
    fields = metadata.split()
    path = raw_path.decode("utf-8", errors="surrogateescape")
    if not separator or path != raw or len(fields) != 3 or fields[1] != b"blob":
        return None
    return fields[0].decode("ascii"), fields[2].decode("ascii")


def index_path_entries(repo: Path, raw: str) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    for payload in git(repo, "ls-files", "--stage", "-z", "--", raw).stdout.split(b"\0"):
        if not payload:
            continue
        metadata, separator, raw_path = payload.partition(b"\t")
        fields = metadata.split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if separator and path == raw and len(fields) == 3:
            result.append(tuple(field.decode("ascii") for field in fields))
    return result


def worktree_source_unchanged(repo: Path, raw: str) -> bool:
    path = repo / raw
    try:
        metadata = path.lstat()
    except OSError:
        return False
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        return False
    head = head_path_entry(repo, raw)
    index = index_path_entries(repo, raw)
    if head is None or len(index) != 1:
        return False
    head_mode, head_blob = head
    index_mode, index_blob, index_stage = index[0]
    if index_stage != "0" or (index_mode, index_blob) != (head_mode, head_blob):
        return False
    worktree_mode = "100755" if metadata.st_mode & 0o111 else "100644"
    if worktree_mode != head_mode:
        return False
    blob = git(repo, "hash-object", f"--path={raw}", "--", raw)
    if blob.returncode or blob.stdout.decode("ascii", errors="replace").strip() != head_blob:
        return False
    return git(repo, "diff", "--quiet", "--no-ext-diff", "HEAD", "--", raw).returncode == 0


def worktree_entries(repo: Path) -> tuple[list[ChangeEntry], list[str]]:
    entries = parse_name_status(
        git(
            repo, "diff", "HEAD", "--name-status", "-z",
            "--find-renames",
        ).stdout
    )
    untracked = sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout.split(b"\0")
        if item
    )
    return entries + [ChangeEntry("A", raw) for raw in untracked], []


def identity_paths(entry: ChangeEntry) -> list[str]:
    return [entry.old_path, entry.path] if entry.status in {"R", "C"} and entry.old_path else [entry.path]


def mutable_paths(entry: ChangeEntry) -> list[str]:
    if entry.status == "C":
        return [entry.path]
    return identity_paths(entry)


def read_only_paths(entry: ChangeEntry) -> list[str]:
    return [entry.old_path] if entry.status == "C" and entry.old_path else []


def path_sets(entries: list[ChangeEntry]) -> dict[str, list[str]]:
    return {
        "identity_paths": sorted({raw for entry in entries for raw in identity_paths(entry)}),
        "mutable_paths": sorted({raw for entry in entries for raw in mutable_paths(entry)}),
        "read_only_paths": sorted({raw for entry in entries for raw in read_only_paths(entry)}),
    }


def path_records(entries: list[ChangeEntry]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for entry in entries:
        if entry.status == "R" and entry.old_path:
            result[entry.old_path] = {"status": "R-old", "peer": entry.path}
            result[entry.path] = {"status": "R-new", "peer": entry.old_path}
        elif entry.status == "C" and entry.old_path:
            result[entry.old_path] = {"status": "C-source", "peer": entry.path, "role": "read-only"}
            result[entry.path] = {"status": "C-destination", "peer": entry.old_path, "role": "mutable"}
        else:
            result[entry.path] = {"status": entry.status, "role": "mutable"}
    return result


def destination_object_id(repo: Path, destination: str, *, staged: bool) -> str | None:
    if staged:
        raw = git(repo, "ls-files", "--stage", "--", destination).stdout.decode(
            "utf-8", errors="replace"
        ).strip()
        if not raw:
            return None
        fields = raw.split()
        return fields[1] if len(fields) >= 2 and fields[0] != "120000" else None
    path = repo / destination
    try:
        metadata = path.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        return None
    result = git(repo, "hash-object", "--no-filters", "--", destination)
    return result.stdout.decode("ascii", errors="replace").strip() if result.returncode == 0 else None


def matching_head_sources(repo: Path, destination: str, *, staged: bool) -> list[str]:
    object_id = destination_object_id(repo, destination, staged=staged)
    return sorted(head_blob_inventory(repo).get(object_id or "", []))


def normalize_for_intent(
    repo: Path, entries: list[ChangeEntry], intended: list[str], *, staged: bool = False,
) -> tuple[list[ChangeEntry], list[str]]:
    intended_set = set(intended)
    errors: list[str] = []
    additions = [entry for entry in entries if entry.status == "A"]
    deleted = {entry.path for entry in entries if entry.status == "D"}
    consumed_additions: set[str] = set()
    consumed_deletions: set[str] = set()
    used_sources: set[str] = set()
    inferred: list[ChangeEntry] = []
    for addition in additions:
        matching = matching_head_sources(repo, addition.path, staged=staged)
        if not matching:
            continue
        explicit = sorted(set(matching) & intended_set)
        relevant = addition.path in intended_set or bool(explicit)
        if not relevant:
            continue
        if len(explicit) != 1:
            if not explicit:
                errors.append(f"exact added destination requires one explicit source peer: {addition.path}")
            else:
                errors.append(
                    f"exact added destination has multiple explicit source peers: {addition.path}: "
                    + ", ".join(explicit)
                )
            continue
        source = explicit[0]
        if source in used_sources:
            errors.append(f"explicit copy/rename source may bind only one destination: {source}")
            continue
        used_sources.add(source); consumed_additions.add(addition.path)
        if source in deleted:
            consumed_deletions.add(source); inferred.append(ChangeEntry("R", addition.path, source))
        elif worktree_source_unchanged(repo, source):
            inferred.append(ChangeEntry("C", addition.path, source))
        else:
            errors.append(f"explicit copy source is not an unchanged regular tracked file: {source}")
    normalized = [
        entry for entry in entries
        if not (entry.status == "A" and entry.path in consumed_additions)
        and not (entry.status == "D" and entry.path in consumed_deletions)
    ] + inferred
    return normalized, sorted(set(errors))


def select_identity(
    repo: Path, entries: list[ChangeEntry], intended: list[str], *, staged: bool = False,
) -> tuple[list[ChangeEntry], list[str]]:
    intended_set = set(intended)
    normalized, errors = normalize_for_intent(repo, entries, intended, staged=staged)
    selected: list[ChangeEntry] = [
        entry for entry in normalized
        if entry.path in intended_set or (entry.status == "R" and entry.old_path in intended_set)
    ]
    covered = {raw for entry in selected for raw in identity_paths(entry)}
    for raw in sorted(intended_set - covered):
        copy_candidates = [
            entry for entry in normalized if entry.status == "C" and entry.old_path == raw
        ]
        if len(copy_candidates) == 1:
            selected.append(copy_candidates[0]); covered.update(identity_paths(copy_candidates[0]))
        elif len(copy_candidates) > 1:
            return selected, [f"copy source is ambiguous without one intended destination: {raw}"]
    unique = list(dict.fromkeys(selected))
    for entry in unique:
        missing = sorted(set(identity_paths(entry)) - intended_set)
        if missing:
            errors.append(
                f"{entry.status} identity requires source and destination: "
                + ", ".join(identity_paths(entry))
            )
    covered = {raw for entry in unique for raw in identity_paths(entry)}
    for raw in sorted(intended_set - covered):
        errors.append(f"intended path has no exact detected change identity: {raw}")
    return unique, sorted(set(errors))


def configure_git(repo: Path) -> None:
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "change-paths@example.invalid")
    git(repo, "config", "user.name", "Change Paths Test")
    git(repo, "config", "core.filemode", "true")


def self_test() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary).resolve(); configure_git(repo)
        source = repo / "iOS/App/Source.swift"; source.parent.mkdir(parents=True)
        source.write_text("struct Source {}\n", encoding="utf-8")
        peer = repo / "iOS/App/Peer.swift"; peer.write_bytes(source.read_bytes())
        cross = repo / "Android/App/Peer.kt"; cross.parent.mkdir(parents=True)
        cross.write_bytes(source.read_bytes())
        git(repo, "add", "."); git(repo, "commit", "-qm", "base")
        baseline = source.read_bytes()
        assert worktree_source_unchanged(repo, "iOS/App/Source.swift")
        source.write_text("staged mutation\n", encoding="utf-8"); git(repo, "add", "iOS/App/Source.swift")
        source.write_bytes(baseline)
        assert not worktree_source_unchanged(repo, "iOS/App/Source.swift")
        git(repo, "reset", "-q", "HEAD", "--", "iOS/App/Source.swift")
        assert worktree_source_unchanged(repo, "iOS/App/Source.swift")
        source.chmod(0o755); git(repo, "add", "iOS/App/Source.swift"); source.chmod(0o644)
        assert not worktree_source_unchanged(repo, "iOS/App/Source.swift")
        git(repo, "reset", "-q", "HEAD", "--", "iOS/App/Source.swift")
        assert worktree_source_unchanged(repo, "iOS/App/Source.swift")
        git(repo, "rm", "--cached", "-q", "--", "iOS/App/Source.swift")
        assert not worktree_source_unchanged(repo, "iOS/App/Source.swift")
        git(repo, "reset", "-q", "HEAD", "--", "iOS/App/Source.swift")
        head_mode, head_blob = head_path_entry(repo, "iOS/App/Source.swift") or ("", "")
        git(repo, "update-index", "--force-remove", "--", "iOS/App/Source.swift")
        unmerged = f"{head_mode} {head_blob} 1\tiOS/App/Source.swift\n{head_mode} {head_blob} 2\tiOS/App/Source.swift\n"
        subprocess.run(
            ["git", "update-index", "--index-info"], cwd=repo,
            input=unmerged, text=True, capture_output=True, check=True,
        )
        assert not worktree_source_unchanged(repo, "iOS/App/Source.swift")
        git(repo, "reset", "-q", "HEAD", "--", "iOS/App/Source.swift")
        source.write_text("unstaged mutation\n", encoding="utf-8")
        assert not worktree_source_unchanged(repo, "iOS/App/Source.swift")
        source.write_bytes(baseline); assert worktree_source_unchanged(repo, "iOS/App/Source.swift")
        destination = repo / "iOS/App/Copy.swift"
        destination.write_bytes(source.read_bytes())
        entries, errors = worktree_entries(repo)
        assert errors == []
        selected, selection_errors = select_identity(
            repo, entries, [source.relative_to(repo).as_posix(), destination.relative_to(repo).as_posix()]
        )
        assert selection_errors == [] and len(selected) == 1 and selected[0].status == "C"
        assert path_sets(selected) == {
            "identity_paths": ["iOS/App/Copy.swift", "iOS/App/Source.swift"],
            "mutable_paths": ["iOS/App/Copy.swift"],
            "read_only_paths": ["iOS/App/Source.swift"],
        }
        assert select_identity(repo, entries, ["iOS/App/Copy.swift"])[1]
        assert select_identity(
            repo, entries, ["iOS/App/Copy.swift", "iOS/App/Source.swift", "iOS/App/Peer.swift"]
        )[1]
        git(repo, "add", "iOS/App/Copy.swift")
        staged = staged_entries(repo)
        staged_selected, staged_errors = select_identity(
            repo, staged, ["iOS/App/Copy.swift", "iOS/App/Source.swift"], staged=True
        )
        assert staged_errors == []
        assert any(entry.status == "C" and entry.old_path == "iOS/App/Source.swift" for entry in staged_selected)
        assert path_sets(staged_selected)["identity_paths"] == ["iOS/App/Copy.swift", "iOS/App/Source.swift"]
    print("git_change_paths self-test: PASS (copy/rename identity vs mutable/read-only sets)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test:
        parser.error("--self-test is required")
    raise SystemExit(self_test())
