#!/usr/bin/env python3
"""Bounded no-follow report snapshot primitive shared by validator and reader."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Callable


MAX_REPORT_BYTES = 1_000_000
READ_CHUNK = 64 * 1024


class ReportError(ValueError):
    pass


def identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def read_report_snapshot(
    path: Path, *, max_bytes: int = MAX_REPORT_BYTES,
    _after_open: Callable[[], None] | None = None,
) -> tuple[bytes, str, int]:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow:
        raise ReportError("platform lacks no-follow report support")
    try:
        path_before = path.lstat()
    except OSError as error:
        raise ReportError("report source metadata is unavailable") from error
    if stat.S_ISLNK(path_before.st_mode) or not stat.S_ISREG(path_before.st_mode):
        raise ReportError("report source must be a regular non-symlink file")
    if path_before.st_size > max_bytes:
        raise ReportError("report source exceeds bounded size")

    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(path_before):
            raise ReportError("report source identity changed before bounded read")
        if _after_open is not None:
            _after_open()
        chunks: list[bytes] = []
        total = 0
        while True:
            remaining = max_bytes + 1 - total
            if remaining <= 0:
                raise ReportError("report source exceeds bounded size")
            chunk = os.read(descriptor, min(READ_CHUNK, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise ReportError("report source exceeds bounded size")
        opened_after = os.fstat(descriptor)
        if identity(opened_after) != identity(opened):
            raise ReportError("report source changed during bounded read")
    except OSError as error:
        raise ReportError("report source cannot be read safely") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    try:
        path_after = path.lstat()
    except OSError as error:
        raise ReportError("report source identity changed after bounded read") from error
    if identity(path_after) != identity(path_before):
        raise ReportError("report source identity changed after bounded read")
    data = b"".join(chunks)
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ReportError("report source must be valid UTF-8 text") from error
    return data, hashlib.sha256(data).hexdigest(), len(data)
