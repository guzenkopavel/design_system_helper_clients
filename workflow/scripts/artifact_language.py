#!/usr/bin/env python3
"""Shared Russian authored-prose validation for lifecycle artifacts."""

from __future__ import annotations

import re
import stat
from pathlib import Path


TECHNICAL_WORDS = {
    "android", "api", "compose", "core", "data", "dynamic", "expressive",
    "glass", "gradle", "ios", "kotlin", "liquid", "material", "sdk", "swift",
    "swiftui", "ui", "ux", "xcode", "materialtheme", "talkback", "watchdog",
    "runtime", "framework", "fallback", "light", "dark", "contrast",
}
MACHINE_STATUSES = {
    "ready", "draft", "approved", "pending", "pass", "fail", "unknown",
    "block", "present", "none", "isolated", "deviation", "not-applicable",
    "done", "gaps", "gap",
}
MACHINE_ROW_LABELS = {
    "Change type", "Shared product spec", "Product status / approval",
    "Product impact assessment", "Product Impact Assessment", "Tier",
    "Selected scopes", "Applicable rule files", "Considered but not selected",
    "Selection snapshot", "UX status", "Platform", "Source product UX",
    "Native design language adapter", "Color direction", "Outcome",
    "Capability triggers", "Physical boundaries",
    "Public contracts and dependency direction", "App-shell responsibilities",
    "App-shell capability ownership", "Repository evidence",
    "Rationale and trade-offs", "Migration boundary and trigger",
    "Over-modularization check", "Boundary guard verdict", "Dependency graph",
    "Public API and visibility", "Module-level tests",
    "Consumer integration and build", "App-shell allowlist", "Layer",
    "Boundary owner", "Engineering scopes", "Depends on", "Status", "Evidence",
    "Estimate (ideal)", "Paths", "Read-only context", "Discovered command",
    "Watchdog max/stall/output budget for nontrivial checks",
    "Applicable rule/check mapping", "Product approval", "Approved by",
    "Applies to", "Source brief",
    "Product review receipt", "UX readiness", "Decision", "Blocking reasons",
}
AUTHORED_ROW_LABELS = {
    "Evidence for each scope", "Considered but not selected", "Selection evidence",
    "Public contracts and dependency direction", "Rationale and trade-offs",
    "Migration boundary and trigger", "Over-modularization check",
    "Approval evidence", "UX artifact",
}
MACHINE_TABLE_HEADERS = {
    "contract id", "layer", "evidence", "evidence path", "status", "path",
    "id", "file", "command", "enum", "key", "value", "requirement",
    "acceptance criteria", "check", "ios", "android", "verification dimension",
    "obligation id", "observation record",
}


def _is_subpath(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def language_residual(raw: str) -> str:
    text = re.sub(r"`[^`\n]*`", " ", raw)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r" \1 ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b(?:REQ|AC|[A-Z][A-Z0-9]*-(?:REQ|AC))-\d+\b", " ", text)
    text = re.sub(r"\btask-\d{3}\b", " ", text, flags=re.I)
    text = re.sub(r"(?<!\w)(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.*/-]+", " ", text)
    text = re.sub(
        r"\b[A-Za-z0-9_-]+\.(?:md|json|swift|kt|kts|xml|toml|yaml|yml|py|sh)\b",
        " ", text, flags=re.I,
    )
    words = re.findall(r"[A-Za-z]+|[А-Яа-яЁё]+", text)
    return " ".join(
        word for word in words
        if word.casefold() not in TECHNICAL_WORDS | MACHINE_STATUSES
        and not (word.isascii() and any(char.isupper() for char in word[1:]))
    )


def authored_markdown_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False
    table_headers: list[str] | None = None

    def flush() -> None:
        if current:
            value = " ".join(current).strip()
            if value:
                blocks.append(value)
            current.clear()

    lines = markdown.splitlines()
    for line_index, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("```") or line.startswith("~~~"):
            flush(); in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line:
            flush(); table_headers = None; continue
        if line.startswith("#") or line.startswith("<!--") or line.endswith("-->"):
            flush(); table_headers = None; continue
        if line.startswith("|"):
            flush()
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            next_line = lines[line_index + 1].strip() if line_index + 1 < len(lines) else ""
            next_cells = [cell.strip() for cell in next_line.strip("|").split("|")] if next_line.startswith("|") else []
            if next_cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in next_cells):
                table_headers = [cell.casefold() for cell in cells]
                continue
            if table_headers and len(table_headers) == len(cells):
                for header, cell in zip(table_headers, cells):
                    if header not in MACHINE_TABLE_HEADERS and cell:
                        current.append(cell); flush()
                continue
            for cell in cells:
                if cell:
                    current.append(cell); flush()
            continue
        list_match = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(.*)$", line)
        stripped = list_match.group(1) if list_match else line
        if list_match:
            flush(); table_headers = None
        label_match = re.match(r"^(?:\*\*)?([^:*]+?)(?:\*\*)?:\s*(.*)$", stripped)
        if label_match and label_match.group(1).strip() in AUTHORED_ROW_LABELS:
            flush(); current.append(label_match.group(2)); flush(); continue
        if label_match and label_match.group(1).strip() in MACHINE_ROW_LABELS:
            flush(); continue
        if re.fullmatch(r"(?:None|None\.|N/A|Covers:\s*\S+)", stripped, re.I):
            flush(); continue
        current.append(stripped)
    flush()
    return blocks


def _english_sentence(raw: str) -> bool:
    """Reject an English natural-language sentence even beside Russian padding."""
    for sentence in re.split(r"(?<=[.!?;])\s+|\n+", raw):
        residual = language_residual(sentence)
        latin = re.findall(r"[A-Za-z]{2,}", residual)
        cyrillic = re.findall(r"[А-Яа-яЁё]{2,}", residual)
        latin_letters = sum(map(len, latin))
        cyrillic_letters = sum(map(len, cyrillic))
        if len(latin) >= 3 and latin_letters >= 12 and latin_letters > cyrillic_letters:
            return True
    return False


def authored_text_is_russian(raw: object) -> bool:
    residual = language_residual(str(raw or ""))
    cyrillic = re.findall(r"[А-Яа-яЁё]{2,}", residual)
    latin = re.findall(r"[A-Za-z]{2,}", residual)
    if not cyrillic and len(latin) < 2:
        return True
    cyrillic_letters = sum(map(len, cyrillic))
    latin_letters = sum(map(len, latin))
    return cyrillic_letters >= 6 and latin_letters <= cyrillic_letters and not _english_sentence(str(raw))


def validate_authored_json_string(value: object, label: str) -> list[str]:
    if authored_text_is_russian(value):
        return []
    return [f"artifact language requires Russian authored JSON prose: {label}"]


def validate_authored_markdown_language(repo: Path, package: Path, path: Path) -> list[str]:
    try:
        repo_relative = path.relative_to(repo)
        label = repo_relative.as_posix()
        package_relative = package.relative_to(repo)
        authored_relative = path.relative_to(package)
    except ValueError:
        return ["artifact language requires safe regular authored Markdown file: <outside-repository>"]
    boundary_error = f"artifact language requires safe regular authored Markdown file: {label}"
    if ".." in package_relative.parts or ".." in authored_relative.parts or ".." in repo_relative.parts:
        return [boundary_error]
    try:
        resolved_repo = repo.resolve(); resolved_package = package.resolve(); resolved_path = path.resolve()
    except (OSError, RuntimeError):
        return [boundary_error]
    if not _is_subpath(resolved_package, resolved_repo) or not _is_subpath(resolved_path, resolved_package):
        return [boundary_error]
    current = repo
    for component in repo_relative.parts:
        current = current / component
        if current.is_symlink():
            return [boundary_error]
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return [boundary_error]
        markdown = path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        return [f"artifact language requires safe UTF-8 authored Markdown file: {label}"]
    except OSError:
        return [boundary_error]
    failing = [
        index for index, block in enumerate(authored_markdown_blocks(markdown), start=1)
        if not authored_text_is_russian(block)
    ]
    if not failing:
        return []
    shown = ", ".join(str(index) for index in failing[:3])
    suffix = f" (+{len(failing) - 3} more)" if len(failing) > 3 else ""
    return [f"artifact language requires Russian authored prose: {label} blocks {shown}{suffix}"]


def self_test() -> int:
    assert authored_text_is_russian("Проверка подтверждает наблюдаемое поведение.")
    assert authored_text_is_russian("Проверяем SwiftUI API и команду xcodebuild.")
    assert not authored_text_is_russian(
        "This sentence is written as natural English prose. "
        "Далее идёт очень длинное русское пояснение, которое не должно компенсировать отдельное английское предложение."
    )
    assert not authored_text_is_russian("This authored rationale describes an unverified outcome.")
    print("artifact-language self-test: PASS (sentence isolation, technical exemptions, JSON prose)")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
