#!/usr/bin/env python3
"""Fail-closed, read-only validator for the deep-code-review public contract."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from deep_code_review_report import MAX_REPORT_BYTES, ReportError, read_report_snapshot


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@{}~^:+-]*$")
SENSITIVE_PARTS = {
    ".env", "id_rsa", "id_ed25519", "local.properties",
}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p8", ".p12", ".jks", ".keystore"}


class ContractError(ValueError):
    """Raised before any review input is read when invocation is unsafe."""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError(message)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def is_subpath(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def safe_repo_path(repo: Path, raw: str, *, must_exist: bool = True) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or not raw.strip():
        raise ContractError(f"unsafe repo-relative path: {raw!r}")
    resolved = (repo / candidate).resolve()
    if not is_subpath(resolved, repo):
        raise ContractError(f"path escapes repository root: {raw!r}")
    lowered = {part.casefold() for part in candidate.parts}
    if (
        lowered & SENSITIVE_PARTS
        or any(part.startswith(".env") for part in lowered)
        or candidate.suffix.casefold() in SENSITIVE_SUFFIXES
    ):
        raise ContractError(f"sensitive report/path is not allowed: {raw!r}")
    if must_exist and not resolved.exists():
        raise ContractError(f"path does not exist: {raw!r}")
    return resolved


def safe_report_candidate(repo: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or not raw.strip():
        raise ContractError(f"unsafe repo-relative path: {raw!r}")
    lowered = {part.casefold() for part in candidate.parts}
    if (
        lowered & SENSITIVE_PARTS
        or any(part.startswith(".env") for part in lowered)
        or candidate.suffix.casefold() in SENSITIVE_SUFFIXES
    ):
        raise ContractError(f"sensitive report/path is not allowed: {raw!r}")
    lexical = repo / candidate
    try:
        parent = lexical.parent.resolve(strict=True)
        parent.relative_to(repo)
    except (OSError, ValueError) as error:
        raise ContractError("report parent escapes repository root") from error
    return parent / lexical.name


def parser() -> Parser:
    root = Parser(prog="validate-deep-code-review.py")
    root.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    modes = root.add_subparsers(dest="mode")

    review = modes.add_parser("review")
    add_identity(review)
    scope = review.add_mutually_exclusive_group()
    scope.add_argument("--against")
    scope.add_argument("--paths", nargs="+")

    feedback = modes.add_parser("feedback")
    add_identity(feedback)
    feedback.add_argument("--report-source", required=True)

    bug = modes.add_parser("bug")
    add_identity(bug)
    bug.add_argument("symptom", nargs="+")

    security = modes.add_parser("security")
    security.add_argument("--json", action="store_true")
    return root


def add_identity(mode: argparse.ArgumentParser) -> None:
    mode.add_argument("platform")
    mode.add_argument("feature")
    mode.add_argument("--change")


def load_adapter(repo: Path, platform: str) -> dict[str, object]:
    matches: list[dict[str, object]] = []
    for path in sorted(repo.glob("*/workflow/platform-contract.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("platform_input", "")).casefold() == platform.casefold():
            matches.append(data)
    if len(matches) != 1:
        raise ContractError(f"platform must resolve to exactly one adapter; found {len(matches)}")
    return matches[0]


def platform_root(repo: Path, adapter: dict[str, object]) -> Path:
    raw = str(adapter.get("platform_root", ""))
    if not raw:
        raise ContractError("adapter platform_root is missing")
    root = safe_repo_path(repo, raw)
    if not root.is_dir():
        raise ContractError("adapter platform_root must be a directory")
    return root


def adapter_secret_globs(adapter: dict[str, object]) -> list[str]:
    pre_commit = adapter.get("pre_commit")
    if not isinstance(pre_commit, dict):
        raise ContractError("adapter pre_commit contract is missing")
    patterns = pre_commit.get("secret_globs")
    if not isinstance(patterns, list) or not patterns:
        raise ContractError("adapter pre_commit.secret_globs is missing")
    result: list[str] = []
    for value in patterns:
        pattern = str(value)
        path = Path(pattern)
        if path.is_absolute() or ".." in path.parts or not pattern.strip():
            raise ContractError("adapter contains unsafe pre_commit.secret_glob")
        result.append(pattern)
    return result


def reject_adapter_secret_path(repo: Path, path: Path, adapter: dict[str, object]) -> None:
    relative = path.relative_to(repo).as_posix()
    for pattern in adapter_secret_globs(adapter):
        direct_pattern = pattern.replace("/**/", "/")
        if fnmatch.fnmatchcase(relative, pattern) or fnmatch.fnmatchcase(relative, direct_pattern):
            raise ContractError(f"path matches adapter secret policy: {relative!r}")


def reject_repository_secret_path(repo: Path, path: Path) -> None:
    contracts = sorted(repo.glob("*/workflow/platform-contract.json"))
    if not contracts:
        raise ContractError("platform adapter contracts are unavailable")
    for contract in contracts:
        try:
            adapter = json.loads(contract.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContractError("platform adapter contract is unreadable") from error
        if not isinstance(adapter, dict):
            raise ContractError("platform adapter contract is invalid")
        reject_adapter_secret_path(repo, path, adapter)


def validate_report_source(
    repo: Path, raw: str, adapter: dict[str, object],
) -> tuple[Path, str, int]:
    path = safe_report_candidate(repo, raw)
    # Secret policy is evaluated before metadata/content access.
    reject_adapter_secret_path(repo, path, adapter)
    reject_repository_secret_path(repo, path)
    try:
        _data, digest, size = read_report_snapshot(path)
    except ReportError as error:
        raise ContractError(str(error)) from error
    return path, digest, size


def resolve_identity(repo: Path, platform: str, feature: str, change: str | None) -> dict[str, str]:
    normalized_platform = platform.casefold()
    if normalized_platform not in {"ios", "android"}:
        raise ContractError("platform must be ios or android")
    if not SLUG_RE.fullmatch(feature):
        raise ContractError("feature must be strict kebab-case")
    adapter = load_adapter(repo, normalized_platform)
    package_root = safe_repo_path(repo, str(adapter.get("package_root", "")), must_exist=False)
    namespace = str(adapter.get("active_changes_namespace", "changes"))
    if not SLUG_RE.fullmatch(namespace):
        raise ContractError("adapter active_changes_namespace is invalid")
    changes = package_root / feature / namespace
    active = []
    if changes.is_dir():
        active = sorted(
            item.name for item in changes.iterdir()
            if item.is_dir() and SLUG_RE.fullmatch(item.name)
            and (item / "meta.json").is_file() and not (item / "ARCHIVED.md").exists()
        )
    if change is None:
        if len(active) != 1:
            raise ContractError(
                f"omitted --change requires exactly one active package; found {len(active)}"
            )
        change = active[0]
    if not SLUG_RE.fullmatch(change):
        raise ContractError("change must be strict kebab-case")
    if change not in active:
        raise ContractError("selected change is not an active package")
    package = (changes / change).resolve()
    if not is_subpath(package, repo):
        raise ContractError("resolved package escapes repository root")
    return {
        "platform": normalized_platform,
        "feature": feature,
        "change": change,
        "package": package.relative_to(repo).as_posix(),
    }


def validate_git_ref(repo: Path, ref: str) -> str:
    if not REF_RE.fullmatch(ref) or ref.startswith("-") or ".." in ref:
        raise ContractError("unsafe git ref")
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        cwd=repo, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        raise ContractError("git ref does not resolve to a commit")
    return ref


def normalize(repo: Path, argv: list[str]) -> dict[str, object]:
    repo = repo.resolve()
    if not repo.is_dir():
        raise ContractError("repository root does not exist")
    if (argv and argv[0] == "fix") or "--fix" in argv:
        raise ContractError("fix mode and --fix are forbidden; deep-code-review is read-only")
    args = parser().parse_args(argv)
    if not args.mode:
        raise ContractError("mode is required")
    if args.mode == "security":
        return {"mode": "security", "json": bool(args.json), "writes_artifacts": []}

    identity = resolve_identity(repo, args.platform, args.feature, args.change)
    adapter = load_adapter(repo, args.platform)
    result: dict[str, object] = {
        "mode": args.mode,
        "identity": identity,
        "writes_artifacts": [],
    }
    if args.mode == "review":
        if args.against:
            result["against"] = validate_git_ref(repo, args.against)
        elif args.paths:
            owner_root = platform_root(repo, adapter)
            selected: list[str] = []
            for raw in args.paths:
                path = safe_repo_path(repo, raw)
                if not is_subpath(path, owner_root):
                    raise ContractError("review --paths must belong to selected adapter platform_root")
                reject_adapter_secret_path(repo, path, adapter)
                selected.append(path.relative_to(repo).as_posix())
            result["paths"] = selected
        else:
            result["scope"] = identity["package"]
    elif args.mode == "feedback":
        if args.report_source == "stdin":
            result["report_source"] = "stdin"
        else:
            report, digest, size = validate_report_source(repo, args.report_source, adapter)
            result["report_source"] = report.relative_to(repo).as_posix()
            result["report_sha256"] = digest
            result["report_size"] = size
    elif args.mode == "bug":
        symptom = " ".join(args.symptom).strip()
        if len(symptom) < 3:
            raise ContractError("symptom-or-finding must be substantive")
        result["symptom"] = symptom
    return result


def make_adapter(repo: Path, name: str) -> None:
    root = repo / name.capitalize() / "workflow"
    root.mkdir(parents=True)
    (root / "platform-contract.json").write_text(json.dumps({
        "platform_input": name,
        "platform_root": name.capitalize(),
        "package_root": f"{name.capitalize()}/specs",
        "active_changes_namespace": "changes",
        "pre_commit": {
            "secret_globs": [f"{name.capitalize()}/**/*.mobileprovision"],
        },
    }), encoding="utf-8")


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        make_adapter(repo, "ios")
        make_adapter(repo, "android")
        package = repo / "Ios/specs/catalog/changes/review-accessibility"
        package.mkdir(parents=True)
        (package / "meta.json").write_text("{}", encoding="utf-8")
        android_package = repo / "Android/specs/catalog/changes/review-accessibility"
        android_package.mkdir(parents=True)
        (android_package / "meta.json").write_text("{}", encoding="utf-8")
        ios_source = repo / "Ios/Sources/Feature.swift"
        ios_source.parent.mkdir(parents=True)
        ios_source.write_text("struct Feature {}", encoding="utf-8")
        android_source = repo / "Android/src/Feature.kt"
        android_source.parent.mkdir(parents=True)
        android_source.write_text("class Feature", encoding="utf-8")
        secret_profile = repo / "Ios/Signing/Test.mobileprovision"
        secret_profile.parent.mkdir(parents=True)
        secret_profile.write_text("must-not-be-read-or-rendered", encoding="utf-8")
        (repo / "safe-report.md").write_text("finding", encoding="utf-8")
        (repo / "report-directory").mkdir()
        (repo / "oversized-report.md").write_bytes(b"x" * (MAX_REPORT_BYTES + 1))
        (repo / "invalid-report.md").write_bytes(b"\xff\xfe")
        (repo / "linked-report.md").symlink_to(repo / "safe-report.md")
        (repo / "README.md").write_text("test", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

        good = normalize(repo, ["review", "ios", "catalog", "--paths", "Ios/Sources/Feature.swift"])
        assert good["identity"]["change"] == "review-accessibility"
        assert normalize(repo, ["review", "android", "catalog", "--paths", "Android/src/Feature.kt"])
        assert normalize(repo, ["feedback", "ios", "catalog", "--report-source", "safe-report.md"])
        assert normalize(repo, ["bug", "ios", "catalog", "button", "does", "not", "respond"])
        assert normalize(repo, ["security", "--json"])["json"] is True

        rejected = [
            ["fix", "ios", "catalog"],
            ["--root", str(repo), "review", "ios", "catalog"],
            ["review", "catalog"],
            ["review", "ios", "catalog", "--paths", "../outside"],
            ["review", "ios", "catalog", "--paths", "Android/src/Feature.kt"],
            ["review", "android", "catalog", "--paths", "Ios/Sources/Feature.swift"],
            ["review", "ios", "catalog", "--paths", "Ios/Signing/Test.mobileprovision"],
            ["feedback", "ios", "catalog", "--report-source", "Ios/Signing/Test.mobileprovision"],
            ["feedback", "android", "catalog", "--report-source", "Ios/Signing/Test.mobileprovision"],
            ["feedback", "ios", "catalog", "--report-source", "report-directory"],
            ["feedback", "ios", "catalog", "--report-source", "oversized-report.md"],
            ["feedback", "ios", "catalog", "--report-source", "invalid-report.md"],
            ["feedback", "ios", "catalog", "--report-source", "linked-report.md"],
            ["feedback", "ios", "catalog", "--report-source", ".env"],
            ["review", "ios", "catalog", "--against", "--bad"],
        ]
        for case in rejected:
            try:
                normalize(repo, case)
            except ContractError:
                pass
            else:
                raise AssertionError(f"unsafe invocation accepted: {case}")

        growing = repo / "growing-report.md"
        growing.write_text("initial", encoding="utf-8")
        def grow_report() -> None:
            with growing.open("ab") as stream:
                stream.write(b"-growth")
        try:
            read_report_snapshot(growing, _after_open=grow_report)
        except ReportError as error:
            assert "initial" not in str(error)
        else:
            raise AssertionError("report growth race accepted")

        swapped = repo / "swapped-report.md"
        replacement = repo / "replacement-report.md"
        swapped.write_text("original-secret-canary", encoding="utf-8")
        replacement.write_text("replacement", encoding="utf-8")
        try:
            read_report_snapshot(swapped, _after_open=lambda: os.replace(replacement, swapped))
        except ReportError as error:
            assert "original-secret-canary" not in str(error)
        else:
            raise AssertionError("report identity swap accepted")

        second = repo / "Ios/specs/catalog/changes/second-change"
        second.mkdir(parents=True)
        (second / "meta.json").write_text("{}", encoding="utf-8")
        try:
            normalize(repo, ["review", "ios", "catalog"])
        except ContractError as error:
            assert "exactly one active package" in str(error)
        else:
            raise AssertionError("ambiguous identity accepted")
    print("validate-deep-code-review self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw == ["--self-test"]:
        return self_test()
    try:
        result = normalize(repository_root(), raw)
    except (ContractError, OSError) as error:
        print(f"deep-code-review contract error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
