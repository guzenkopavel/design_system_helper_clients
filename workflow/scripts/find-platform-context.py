#!/usr/bin/env python3
"""Build a small adapter-backed context packet for a platform feature."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import tempfile
from pathlib import Path

from platform_rule_profiles import RuleProfileError, require_capability, rules_for_phase, validate_profiles

BASE_EXCLUDED = {".git", "_archive"}
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
            validate_profiles(repo, data)
            return data
    return None


def collect_candidates(
    repo: Path, adapter: dict[str, object], feature: str,
    platform_root: Path, package_root: Path,
) -> list[tuple[Path, str, str]]:
    raw_suffixes = adapter.get("context_file_suffixes")
    raw_excluded = adapter.get("context_excluded_directories")
    raw_globs = adapter.get("context_always_include_globs")
    if (
        not isinstance(raw_suffixes, list) or not raw_suffixes
        or not all(isinstance(item, str) and re.fullmatch(r"\.[a-z0-9]+", item) for item in raw_suffixes)
        or not isinstance(raw_excluded, list)
        or not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9._-]+", item) for item in raw_excluded)
        or not isinstance(raw_globs, list) or not raw_globs
        or not all(
            isinstance(item, str) and not Path(item).is_absolute()
            and ".." not in Path(item).parts
            and re.fullmatch(r"[A-Za-z0-9_./*?-]+", item)
            for item in raw_globs
        )
    ):
        raise ValueError("adapter context discovery fields are invalid")
    context_suffixes = set(str(item) for item in raw_suffixes)
    excluded = BASE_EXCLUDED | {str(item) for item in raw_excluded}
    needles = {feature.lower(), feature.replace("-", " ").lower()}
    bases = [repo / "specs" / "product", package_root, repo / "workflow", platform_root / "workflow", platform_root]
    candidates: list[tuple[Path, str, str]] = []
    seen: set[Path] = set()
    for pattern in raw_globs:
        for path in sorted(repo.glob(str(pattern))):
            resolved = path.resolve()
            if not path.is_file() or not is_subpath(resolved, repo) or any(part in excluded for part in path.parts):
                continue
            seen.add(path)
            candidates.append((path.relative_to(repo), "adapter always-include", "context"))
    for base in bases:
        if not base.exists():
            continue
        for current, dirs, files in os.walk(base):
            archive_namespace = str(adapter.get("archive_namespace", "archive"))
            dirs[:] = [d for d in dirs if d not in excluded and d != archive_namespace and not d.startswith(".")]
            for name in files:
                path = Path(current) / name
                if path in seen or path.suffix.lower() not in context_suffixes:
                    continue
                seen.add(path)
                rel = path.relative_to(repo)
                reason = "path match" if any(n in str(rel).lower() for n in needles) else ""
                if not reason and path.stat().st_size <= 1_000_000:
                    try:
                        content = path.read_text(encoding="utf-8", errors="ignore").lower()
                    except OSError:
                        continue
                    if any(n in content for n in needles):
                        reason = "content match"
                if reason:
                    is_context = (
                        str(rel).startswith("workflow/")
                        or str(rel).startswith("specs/")
                        or str(rel).startswith(f"{adapter['platform_root']}/workflow/")
                        or str(rel).startswith(f"{adapter['package_root']}/")
                    )
                    candidates.append((rel, reason, "context" if is_context else "source"))
    return candidates


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve()
        validator_path = Path(__file__).with_name("validate-platform-change.py")
        spec = importlib.util.spec_from_file_location("context_fixture_validator", validator_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load fixture validator")
        validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
        adapter, _package, _meta = validator.write_fixture(repo)
        manifest = repo / "TestClient/App/Package.swift"; manifest.parent.mkdir(parents=True); manifest.write_text("// project configuration\n")
        candidates = collect_candidates(
            repo, adapter, "unrelated-greenfield-feature",
            repo / str(adapter["platform_root"]), repo / str(adapter["package_root"]),
        )
        assert any(path == Path("TestClient/App/Package.swift") and reason == "adapter always-include" for path, reason, _ in candidates)
    print("find-platform-context self-test: PASS (greenfield always-include project context)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform")
    parser.add_argument("--feature")
    parser.add_argument("--change")
    parser.add_argument("--phase", choices=("propose", "plan", "implement", "verify"))
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.platform or not args.feature or not args.phase:
        parser.error("--platform, --feature and --phase are required")
    if not FEATURE_RE.fullmatch(args.feature):
        print("BLOCKED: feature must be a strict kebab-case slug; no files were written.")
        return 3
    change_id = args.change or args.feature
    if not FEATURE_RE.fullmatch(change_id):
        print("BLOCKED: change_id must be a strict kebab-case slug; no files were written.")
        return 3
    repo = root()
    try:
        adapter = load_adapter(repo, args.platform)
    except RuleProfileError as error:
        print(f"BLOCKED: invalid platform rule profiles: {error}; no files were written.")
        return 4
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
    try:
        require_capability(adapter, args.phase)
        scopes, exact_rules = rules_for_phase(repo, adapter, args.phase, args.scope)
    except RuleProfileError as error:
        print(f"BLOCKED: {error}.")
        return 4
    try:
        candidates = collect_candidates(repo, adapter, args.feature, platform_root, package_root)
    except ValueError as error:
        print(f"BLOCKED: {error}; no files were written.")
        return 4

    print("Retrieval Packet")
    print(
        f"Platform: {platform_name}\nFeature: {args.feature}\nChange ID: {change_id}\n"
        f"Phase: {args.phase}\nEngineering scopes: {', '.join(scopes) if scopes else 'none selected'}\n"
        "Confidence: evidence-backed paths only"
    )
    print("\nExact applicable phase rules:")
    for rule in exact_rules:
        print(f"- {rule}")
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
    proposed = package_root / args.feature / str(adapter.get("active_changes_namespace", "changes")) / change_id
    print("\nExcluded: generated/build/vendor noise and other platform surfaces.")
    print(
        f"Proposed package: {proposed.relative_to(repo)}/ "
        "(not evidence of source-code existence)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
