#!/usr/bin/env python3
"""Canonical fail-closed platform writable-path ownership checks."""

from __future__ import annotations

import argparse
import stat
import tempfile
from pathlib import Path, PurePosixPath


class PathOwnershipError(ValueError):
    pass


def normalize_repo_relative(raw: str) -> str:
    if not isinstance(raw, str) or "\0" in raw:
        raise PathOwnershipError("platform writable path must be a plain repo-relative string")
    value = PurePosixPath(raw)
    if value.is_absolute() or ".." in value.parts or value.as_posix() in {"", "."}:
        raise PathOwnershipError(f"platform writable path must be safe and repo-relative: {raw}")
    return value.as_posix()


def path_under(raw: str, roots: list[str]) -> bool:
    value = PurePosixPath(raw)
    return any(value == PurePosixPath(root) or PurePosixPath(root) in value.parents for root in roots)


def paths_overlap(left: str, right: str) -> bool:
    lhs = PurePosixPath(left); rhs = PurePosixPath(right)
    return lhs == rhs or lhs in rhs.parents or rhs in lhs.parents


def lexical_adapter_candidate(adapter: dict[str, object], raw: str) -> bool:
    try:
        normalized = normalize_repo_relative(raw)
    except PathOwnershipError:
        return False
    return path_under(normalized, [str(item) for item in adapter.get("production_roots", [])])


def first_symlink(repo: Path, normalized: str) -> str | None:
    current = repo
    for part in PurePosixPath(normalized).parts:
        current /= part
        if current.is_symlink():
            return current.relative_to(repo).as_posix()
        if not current.exists():
            break
    return None


def canonical_repo_relative(repo: Path, raw: str, label: str) -> str:
    """Resolve a boundary without allowing an existing symlink component."""
    normalized = normalize_repo_relative(raw)
    symlink = first_symlink(repo, normalized)
    if symlink is not None:
        raise PathOwnershipError(f"{label} may not traverse symlinks: {normalized} via {symlink}")
    target = repo / normalized
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        mode = None
    if mode is not None and stat.S_ISLNK(mode):
        raise PathOwnershipError(f"{label} may not be a symlink: {normalized}")
    try:
        return target.resolve(strict=False).relative_to(repo).as_posix()
    except ValueError as error:
        raise PathOwnershipError(f"{label} resolves outside repository: {normalized}") from error


def validate_platform_writable_path(
    repo: Path, adapter: dict[str, object], raw: str, *, require_existing: bool = False,
) -> str:
    """Validate lexical and canonical ownership with a no-symlink writable policy."""
    repo = repo.resolve()
    normalized = normalize_repo_relative(raw)
    production = [str(item) for item in adapter.get("production_roots", [])]
    denied = [
        str(item)
        for item in adapter.get("protected_roots", []) + adapter.get("production_exclusions", [])
    ]
    if not path_under(normalized, production):
        raise PathOwnershipError(f"path is outside selected platform production ownership: {normalized}")
    if any(paths_overlap(normalized, boundary) for boundary in denied):
        raise PathOwnershipError(f"path overlaps protected/excluded boundary of selected platform: {normalized}")
    resolved_relative = canonical_repo_relative(repo, normalized, "platform writable path")
    target = repo / normalized
    if require_existing and not target.exists():
        raise PathOwnershipError(f"existing platform writable path does not exist: {normalized}")
    canonical_production = [canonical_repo_relative(repo, root, "production boundary") for root in production]
    if not path_under(resolved_relative, canonical_production):
        raise PathOwnershipError(
            f"platform writable path resolves outside selected production ownership: {normalized}"
        )
    canonical_denied: list[str] = []
    for boundary in denied:
        canonical_denied.append(canonical_repo_relative(repo, boundary, "protected/excluded boundary"))
    if any(paths_overlap(resolved_relative, boundary) for boundary in canonical_denied):
        raise PathOwnershipError(
            f"platform writable path resolves into protected/excluded boundary: {normalized}"
        )
    return normalized


def self_test() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary).resolve()
        ios = {
            "production_roots": ["iOS/App"],
            "protected_roots": ["iOS/specs", "iOS/workflow"],
            "production_exclusions": ["iOS/specs", "iOS/workflow"],
        }
        android = {
            "production_roots": ["Android/App"],
            "protected_roots": ["Android/specs", "Android/workflow"],
            "production_exclusions": ["Android/specs", "Android/workflow"],
        }
        for relative in ("iOS/App", "iOS/specs", "iOS/workflow", "Android/App", "Android/specs", "Android/workflow"):
            (repo / relative).mkdir(parents=True, exist_ok=True)
        (repo / "iOS/App/Owned.swift").write_text("owned\n", encoding="utf-8")
        assert validate_platform_writable_path(repo, ios, "iOS/App/Owned.swift", require_existing=True) == "iOS/App/Owned.swift"
        assert validate_platform_writable_path(repo, android, "Android/App/New.kt") == "Android/App/New.kt"

        outside = repo.parent / f"{repo.name}-outside.swift"
        outside.write_text("outside\n", encoding="utf-8")
        try:
            (repo / "iOS/App/FileLink.swift").symlink_to(outside)
            for adapter, candidate in (
                (ios, "iOS/App/FileLink.swift"),
                (ios, "iOS/App/DirectoryLink/Child.swift"),
                (android, "Android/App/DirectoryLink/Proposed.kt"),
            ):
                if "DirectoryLink" in candidate:
                    link = repo / PurePosixPath(candidate).parent
                    if not link.exists() and not link.is_symlink():
                        target = repo / ("Android/App" if adapter is ios else "iOS/App")
                        link.symlink_to(target, target_is_directory=True)
                try:
                    validate_platform_writable_path(repo, adapter, candidate)
                except PathOwnershipError as error:
                    assert "symlink" in str(error)
                else:
                    raise AssertionError(f"symlink writable escape accepted: {candidate}")
        finally:
            outside.unlink(missing_ok=True)
    print("platform_path_ownership self-test: PASS (iOS/Android file, directory, proposed-child symlinks)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test:
        parser.error("--self-test is required")
    raise SystemExit(self_test())
