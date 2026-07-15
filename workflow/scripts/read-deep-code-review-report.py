#!/usr/bin/env python3
"""Read a validated feedback report only when its bounded snapshot still matches."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from deep_code_review_report import ReportError, read_report_snapshot


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReaderError(ValueError):
    pass


def repository_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, check=False,
    )
    if completed.returncode:
        raise ReaderError("repository root is unavailable")
    return Path(os.fsdecode(completed.stdout.strip())).resolve()


def safe_path(repo: Path, raw: str) -> Path:
    value = PurePosixPath(raw)
    if value.is_absolute() or ".." in value.parts or not raw.strip():
        raise ReaderError("report path must be safe and repo-relative")
    lexical = repo.joinpath(*value.parts)
    try:
        parent = lexical.parent.resolve(strict=True)
        parent.relative_to(repo)
    except (OSError, ValueError) as error:
        raise ReaderError("report parent escapes repository root") from error
    return parent / lexical.name


def read_bound(repo: Path, raw: str, expected_sha256: str, expected_size: int) -> bytes:
    if not SHA256_RE.fullmatch(expected_sha256) or expected_size < 0:
        raise ReaderError("expected report identity is invalid")
    path = safe_path(repo.resolve(), raw)
    try:
        data, digest, size = read_report_snapshot(path)
    except ReportError as error:
        raise ReaderError(str(error)) from error
    if digest != expected_sha256 or size != expected_size:
        raise ReaderError("report no longer matches validated identity")
    return data


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve()
        report = repo / "report.md"
        report.write_text("safe finding", encoding="utf-8")
        data = report.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        assert read_bound(repo, "report.md", digest, len(data)) == data
        try:
            read_bound(repo, "report.md", "0" * 64, len(data))
        except ReaderError:
            pass
        else:
            raise AssertionError("hash mismatch accepted")
        replacement = repo / "replacement.md"
        replacement.write_text("replacement", encoding="utf-8")
        os.replace(replacement, report)
        try:
            read_bound(repo, "report.md", digest, len(data))
        except ReaderError:
            pass
        else:
            raise AssertionError("replacement report accepted")
        report.unlink()
        report.symlink_to(repo / "outside.md")
        try:
            read_bound(repo, "report.md", digest, len(data))
        except ReaderError:
            pass
        else:
            raise AssertionError("final-component symlink accepted")
    print("read-deep-code-review-report self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("path", nargs="?")
    cli.add_argument("--expected-sha256")
    cli.add_argument("--expected-size", type=int)
    args = cli.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        if args.path is None or args.expected_sha256 is None or args.expected_size is None:
            raise ReaderError("path, --expected-sha256 and --expected-size are required")
        data = read_bound(repository_root(), args.path, args.expected_sha256, args.expected_size)
    except (ReaderError, OSError) as error:
        print(f"report reader error: {error}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
