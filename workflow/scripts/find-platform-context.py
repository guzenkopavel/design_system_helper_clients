#!/usr/bin/env python3
"""Build a small adapter-backed context packet for a platform feature."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

EXCLUDED = {
    ".git",
    ".build",
    ".gradle",
    ".swiftpm",
    "DerivedData",
    "build",
    "node_modules",
}
FEATURE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def root() -> Path:
    return Path(__file__).resolve().parents[2]


def is_subpath(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def safe_root(repo: Path, raw: str) -> Path | None:
    value = Path(raw)
    if value.is_absolute() or ".." in value.parts:
        return None
    resolved = (repo / value).resolve()
    return resolved if is_subpath(resolved, repo) else None


def load_adapter(repo: Path, platform: str) -> dict[str, object] | None:
    for path in sorted(repo.glob("*/workflow/platform-contract.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("platform_input", "")).lower() == platform.lower():
            return data
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if not FEATURE_RE.fullmatch(args.feature):
        print("BLOCKED: feature must be a strict kebab-case slug; no files were written.")
        return 3
    repo = root()
    adapter = load_adapter(repo, args.platform)
    if adapter is None:
        print(
            f"BLOCKED: NOT IMPLEMENTED: platform '{args.platform}' has no implementation adapter; "
            "no files were written."
        )
        return 4
    platform_name = str(adapter.get("platform_name", args.platform))
    platform_root = safe_root(repo, str(adapter.get("platform_root", "")))
    package_root = safe_root(repo, str(adapter.get("package_root", "")))
    if platform_root is None or package_root is None:
        print("BLOCKED: platform adapter contains an unsafe path; no files were written.")
        return 4

    needles = {args.feature.lower(), args.feature.replace("-", " ").lower()}
    bases = [
        repo / "specs" / "product",
        package_root,
        repo / "workflow",
        platform_root / "workflow",
        platform_root,
    ]
    candidates: list[tuple[Path, str, str]] = []
    seen: set[Path] = set()
    for base in bases:
        if not base.exists():
            continue
        for current, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUDED and not d.startswith(".")]
            for name in files:
                path = Path(current) / name
                if path in seen or path.suffix.lower() not in {
                    ".md",
                    ".json",
                    ".swift",
                    ".xcodeproj",
                    ".toml",
                    ".yaml",
                    ".yml",
                }:
                    continue
                seen.add(path)
                rel = path.relative_to(repo)
                reason = "path match" if any(n in str(rel).lower() for n in needles) else ""
                if not reason and path.stat().st_size <= 1_000_000:
                    try:
                        text = path.read_text(encoding="utf-8", errors="ignore").lower()
                    except OSError:
                        continue
                    if any(n in text for n in needles):
                        reason = "content match"
                if reason:
                    is_context = (
                        str(rel).startswith("workflow/")
                        or str(rel).startswith("specs/")
                        or str(rel).startswith(f"{adapter['platform_root']}/workflow/")
                        or str(rel).startswith(f"{adapter['package_root']}/")
                    )
                    category = "context" if is_context else "source"
                    candidates.append((rel, reason, category))

    print("Retrieval Packet")
    print(
        f"Platform: {platform_name}\nFeature: {args.feature}\n"
        "Confidence: evidence-backed paths only"
    )
    limited = sorted(candidates)[: args.limit]
    context_hits = [(rel, reason) for rel, reason, category in limited if category == "context"]
    source_hits = [(rel, reason) for rel, reason, category in limited if category == "source"]
    print("\nExisting context documents:")
    for rel, reason in context_hits:
        print(f"- {rel} — {reason}")
    if not context_hits:
        print("- none")
    print("\nVerified existing source files:")
    for rel, reason in source_hits:
        print(f"- {rel} — {reason}")
    if not source_hits:
        print("- none; treat implementation paths as proposed greenfield paths")
    proposed = package_root / args.feature
    print("\nExcluded: generated/build/vendor noise and other platform surfaces.")
    print(
        f"Proposed package: {proposed.relative_to(repo)}/ "
        "(not evidence of source-code existence)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
