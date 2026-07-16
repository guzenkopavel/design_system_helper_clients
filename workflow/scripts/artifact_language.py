#!/usr/bin/env python3
"""Shared Russian authored-prose validation for lifecycle artifacts."""

from __future__ import annotations

import re
import shlex
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
TASK_EVIDENCE_SUMMARY_HEADINGS = {
    "Итог", "Резюме", "Результат", "Результат проверки", "Summary",
}
TASK_EVIDENCE_RAW_HEADINGS = {
    "Технические доказательства",
    "Changed paths",
}
TASK_EVIDENCE_CANONICAL_RAW_HEADING = "Технические доказательства"
TASK_EVIDENCE_COMMAND_PATTERNS = (
    re.compile(r"^rtk bash workflow/scripts/[A-Za-z0-9_./-]+\.sh(?=\s|$)"),
    re.compile(r"^rtk python3 workflow/scripts/[A-Za-z0-9_./-]+\.py(?=\s|$)"),
    re.compile(r"^rtk git (?:status|diff|show|ls-files|rev-parse|check-ignore)(?=\s|$)"),
    re.compile(r"^rtk \./Android/gradlew(?=\s|$)"),
    re.compile(r"^rtk swift (?:test|build|package)(?=\s|$)"),
    re.compile(r"^rtk xcodebuild(?=\s|$)"),
    re.compile(r"^rtk xcrun (?:simctl|xcresulttool)(?=\s|$)"),
)
TASK_EVIDENCE_COMMAND_ENUMS = {
    "Android", "Debug", "HEAD", "PASS", "Release", "android", "archive",
    "check", "describe", "implement", "ios", "plain", "plan", "projects",
    "propose", "resolve", "snapshot", "tasks", "update", "verify",
}
TASK_EVIDENCE_COMMAND_OPTIONS = {
    "--", "--all", "--apply", "--baseline", "--cached", "--change",
    "--console", "--derivedDataPath", "--destination", "--diff-filter",
    "--dry-run", "--expected-sha256", "--feature", "--json",
    "--max-output-lines", "--max-seconds", "--mode", "--name-only",
    "--no-daemon", "--output", "--package-path", "--path", "--phase",
    "--platform", "--porcelain", "--project", "--quiet", "--resultBundlePath",
    "--root", "--scheme", "--scope", "--sdk", "--self-test",
    "--stall-seconds", "--task", "--untracked-files", "--workspace",
    "-C", "-configuration", "-destination", "-p", "-project", "-q",
    "-scheme", "-sdk", "-workspace",
}
TASK_EVIDENCE_TECHNICAL_ANNOTATION_WORDS = {
    "adapter", "api", "asset", "assets", "availability", "build", "case",
    "client", "config", "configuration", "contract", "dependency", "dto",
    "email", "fixture", "implementation", "interface", "manifest",
    "migration", "mock", "model", "module", "package", "project",
    "protocol", "provider", "repository", "resource", "route", "routing",
    "schema", "screen", "service", "source", "storage", "store", "stub",
    "target", "test", "tests", "use", "view", "wiring", "workspace",
}
TASK_EVIDENCE_TECHNICAL_ANNOTATION_MAX_TOKENS = 7


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


def _read_safe_authored_markdown(
    repo: Path, package: Path, path: Path,
) -> tuple[str | None, str, list[str]]:
    try:
        repo_relative = path.relative_to(repo)
        label = repo_relative.as_posix()
        package_relative = package.relative_to(repo)
        authored_relative = path.relative_to(package)
    except ValueError:
        error = "artifact language requires safe regular authored Markdown file: <outside-repository>"
        return None, "<outside-repository>", [error]
    boundary_error = f"artifact language requires safe regular authored Markdown file: {label}"
    if ".." in package_relative.parts or ".." in authored_relative.parts or ".." in repo_relative.parts:
        return None, label, [boundary_error]
    try:
        resolved_repo = repo.resolve(); resolved_package = package.resolve(); resolved_path = path.resolve()
    except (OSError, RuntimeError):
        return None, label, [boundary_error]
    if not _is_subpath(resolved_package, resolved_repo) or not _is_subpath(resolved_path, resolved_package):
        return None, label, [boundary_error]
    current = repo
    for component in repo_relative.parts:
        current = current / component
        if current.is_symlink():
            return None, label, [boundary_error]
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return None, label, [boundary_error]
        markdown = path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, label, [f"artifact language requires safe UTF-8 authored Markdown file: {label}"]
    except OSError:
        return None, label, [boundary_error]
    return markdown, label, []


def _markdown_language_errors(markdown: str, label: str) -> list[str]:
    failing = [
        index for index, block in enumerate(authored_markdown_blocks(markdown), start=1)
        if not authored_text_is_russian(block)
    ]
    if not failing:
        return []
    shown = ", ".join(str(index) for index in failing[:3])
    suffix = f" (+{len(failing) - 3} more)" if len(failing) > 3 else ""
    return [f"artifact language requires Russian authored prose: {label} blocks {shown}{suffix}"]


def validate_authored_markdown_language(repo: Path, package: Path, path: Path) -> list[str]:
    markdown, label, errors = _read_safe_authored_markdown(repo, package, path)
    if errors or markdown is None:
        return errors
    return _markdown_language_errors(markdown, label)


def _task_evidence_sections(markdown: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Split H1/H2 task sections while retaining prose before the first heading."""
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    for raw in markdown.splitlines():
        match = re.fullmatch(r"#{1,2}[ \t]+(.+?)[ \t]*", raw)
        if match:
            heading = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(1)).strip()
            current = []
            sections.append((heading, current))
        elif current is None:
            preamble.append(raw)
        else:
            current.append(raw)
    return preamble, sections


def _substantive_russian_summary(raw: str) -> bool:
    blocks = authored_markdown_blocks(raw)
    if not blocks or any(not authored_text_is_russian(block) for block in blocks):
        return False
    residual = language_residual(" ".join(blocks))
    words = re.findall(r"[А-Яа-яЁё]{2,}", residual)
    return (
        len(words) >= 3
        and sum(map(len, words)) >= 12
    )


def _strip_task_evidence_line_prefix(raw: str) -> str:
    value = raw.rstrip()
    value = re.sub(r"^\s*[-*+]\s+", "", value)
    value = re.sub(r"^(?:[ MADRCU?!]{2}|[AMDRCU]\d{1,3})[ \t]+", "", value)
    return value.strip()


def _safe_repo_relative_path(raw: str) -> bool:
    value = raw.strip().strip("`").rstrip("/")
    if not value or value.startswith(("/", "~")) or "\\" in value.replace(r"\ ", ""):
        return False
    parts = value.split("/")
    if len(parts) < 2 or any(part in {"", ".", ".."} for part in parts):
        return False
    return all(
        len(part) <= 180
        and re.fullmatch(r"[A-Za-z0-9_.@+-]+(?:\\ [A-Za-z0-9_.@+-]+)*", part) is not None
        for part in parts
    )


def _task_evidence_path_row(raw: str) -> bool:
    value = _strip_task_evidence_line_prefix(raw)
    if not value:
        return False
    split_annotation = re.split(r"\s+(?:—|–|-)\s+", value, maxsplit=1)
    path_expression = split_annotation[0].strip()
    if len(split_annotation) == 2:
        annotation = split_annotation[1].strip()
        if (
            not annotation or len(annotation) > 160
            or re.search(r"[.!?;]", annotation)
            or re.search(r"https?://", annotation, re.I)
            or not _task_evidence_technical_annotation(annotation)
        ):
            return False
    rename_paths = re.split(r"\s+(?:->|→)\s+", path_expression)
    return len(rename_paths) in {1, 2} and all(
        _safe_repo_relative_path(item) for item in rename_paths
    )


def _task_evidence_code_identifier(raw: str) -> bool:
    return (
        re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]*", raw) is not None
        and (
            raw.isupper()
            or any(character.isupper() for character in raw[1:])
            or any(marker in raw for marker in ("_", ".", ":"))
            or any(character.isdigit() for character in raw)
        )
    )


def _task_evidence_technical_annotation(raw: str) -> bool:
    tokens = raw.split()
    if not 1 <= len(tokens) <= TASK_EVIDENCE_TECHNICAL_ANNOTATION_MAX_TOKENS:
        return False
    for token in tokens:
        folded = token.casefold()
        if folded in TASK_EVIDENCE_TECHNICAL_ANNOTATION_WORDS:
            continue
        hyphen_parts = token.split("-")
        if len(hyphen_parts) > 1 and all(hyphen_parts) and all(
            part.casefold() in TASK_EVIDENCE_TECHNICAL_ANNOTATION_WORDS
            for part in hyphen_parts
        ):
            continue
        if _task_evidence_code_identifier(token):
            continue
        return False
    return True


def _task_evidence_command_value(raw: str) -> bool:
    if raw in TASK_EVIDENCE_COMMAND_ENUMS:
        return True
    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return True
    if re.fullmatch(r"[0-9a-fA-F]{7,64}", raw):
        return True
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", raw):
        return True
    if re.fullmatch(r"\.?\.?/(?:[A-Za-z0-9_.@+-]+/)*[A-Za-z0-9_.@+-]+", raw):
        return True
    if re.fullmatch(r"(?:[A-Za-z0-9_.@+-]+/)+[A-Za-z0-9_.@+-]+", raw):
        return True
    return _task_evidence_code_identifier(raw)


def _task_evidence_command_line(raw: str) -> bool:
    value = raw.strip()
    value = re.sub(r"^(?:[-*+]\s+)", "", value)
    value = re.sub(r"^(?:Command|Команда):\s*", "", value)
    value = re.sub(r"^\$\s+", "", value)
    for pattern in TASK_EVIDENCE_COMMAND_PATTERNS:
        match = pattern.match(value)
        if match is None:
            continue
        try:
            arguments = shlex.split(value[match.end():].strip())
        except ValueError:
            return False
        for argument in arguments:
            if not re.fullmatch(r"[A-Za-z0-9_./:=@+, -]+", argument):
                return False
            if argument.startswith("-"):
                option_name = argument.split("=", 1)[0]
                if option_name not in TASK_EVIDENCE_COMMAND_OPTIONS:
                    return False
                if "=" in argument:
                    _flag, value_part = argument.split("=", 1)
                    if not value_part or not _task_evidence_command_value(value_part):
                        return False
                continue
            if not _task_evidence_command_value(argument):
                return False
        return True
    return False


def _authored_task_evidence_raw_lines(heading: str, body: list[str]) -> list[str]:
    authored: list[str] = []
    in_fence = False
    for raw in body:
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            authored.append(raw)
            in_fence = not in_fence
            continue
        if in_fence:
            authored.append(raw)
            continue
        if not stripped:
            authored.append(raw)
            continue
        if _task_evidence_path_row(raw):
            continue
        if (
            heading == TASK_EVIDENCE_CANONICAL_RAW_HEADING
            and _task_evidence_command_line(raw)
        ):
            continue
        authored.append(raw)
    return authored


def validate_task_evidence_language(repo: Path, package: Path, path: Path) -> list[str]:
    """Validate typed task evidence with bounded raw technical sections."""
    markdown, label, errors = _read_safe_authored_markdown(repo, package, path)
    if errors or markdown is None:
        return errors
    preamble, sections = _task_evidence_sections(markdown)
    summaries = [body for heading, body in sections if heading in TASK_EVIDENCE_SUMMARY_HEADINGS]
    if len(summaries) != 1:
        errors.append(
            f"task evidence requires exactly one Russian summary section: {label}"
        )
    elif not _substantive_russian_summary("\n".join(summaries[0])):
        errors.append(f"task evidence requires substantive Russian summary: {label}")

    authored_lines = list(preamble)
    for heading, body in sections:
        if heading in TASK_EVIDENCE_RAW_HEADINGS:
            authored_lines.append(f"## {heading}")
            authored_lines.extend(_authored_task_evidence_raw_lines(heading, body))
            continue
        authored_lines.append(f"## {heading}")
        authored_lines.extend(body)
    errors.extend(_markdown_language_errors("\n".join(authored_lines), label))
    return errors


def self_test() -> int:
    assert authored_text_is_russian("Проверка подтверждает наблюдаемое поведение.")
    assert authored_text_is_russian("Проверяем SwiftUI API и команду xcodebuild.")
    assert not authored_text_is_russian(
        "This sentence is written as natural English prose. "
        "Далее идёт очень длинное русское пояснение, которое не должно компенсировать отдельное английское предложение."
    )
    assert not authored_text_is_russian("This authored rationale describes an unverified outcome.")
    import tempfile

    with tempfile.TemporaryDirectory() as raw_tmp:
        repo = Path(raw_tmp).resolve()
        package = repo / "iOS/specs/sample/changes/sample"
        evidence = package / "evidence"
        evidence.mkdir(parents=True)
        report = evidence / "task-001.md"

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Реализация добавляет проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "iOS/Feature/Sources/VeryLong/AuthAPIClient.swift — API client contract\n"
            " M iOS/Feature/Sources/VeryLong/CheckEmailUseCase.swift\n"
            "rtk swift test --package-path iOS/Feature\n"
            "```text\nBuild completed with no compiler errors.\n```\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report) == []

        report.write_text(
            "# Итог\n\n"
            "Реализация добавляет проверенный контракт авторизации.\n\n"
            "# Проверки\n\nФокусированная проверка завершилась успешно.\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report) == []

        report.write_text(
            "# Итог\n\nThis authored summary remains entirely English.\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# Итог\n\nПервый русский итог описывает результат задачи.\n\n"
            "## Резюме\n\nВторой русский итог недопустимо дублирует первый.\n",
            encoding="utf-8",
        )
        duplicate_summary_errors = validate_task_evidence_language(
            repo, package, report,
        )
        assert any("exactly one Russian summary section" in item for item in duplicate_summary_errors)

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Реализация добавляет проверенный контракт авторизации.\n\n"
            "## Changed paths\n\n"
            "iOS/Feature/Sources/VeryLong/AuthAPIClient.swift — API client contract\n"
            "iOS/Feature/Sources/VeryLong/CheckEmailUseCase.swift — email availability use case\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report) == []

        report.write_text(
            "# task-001\n\n## Summary\n\n"
            "This authored summary describes a completed task result.\n\n"
            "## Changed paths\n\nlong/path/AuthAPIClient.swift — API contract\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Результат\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Unknown notes\n\nThis authored section remains entirely English.\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        for heading in TASK_EVIDENCE_RAW_HEADINGS:
            report.write_text(
                "# task-001\n\n## Резюме\n\n"
                "Задача реализует проверенный контракт авторизации.\n\n"
                f"## {heading}\n\n"
                "very/long/path/AuthAPIClient.swift — English technical annotation\n"
                "Tests were not run. Known limitation remains.\n",
                encoding="utf-8",
            )
            assert validate_task_evidence_language(repo, package, report), heading

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Changed paths\n\n"
            "very/long/path/AuthAPIClient.swift — API client contract\n"
            "rtk swift test --package-path iOS/Feature\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "very/long/path/AuthAPIClient.swift — API client contract\n"
            "rtk swift test --package-path iOS/Feature\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report) == []

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "rtk swift test Tests were not run\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "very/long/path/AuthAPIClient.swift — Known limitation remains.\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "very/long/path/AuthAPIClient.swift — "
            "Tests were not run because simulator unavailable and known limitations remain unresolved\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "rtk python3 workflow/scripts/tool.py --feature user-profile-auth "
            "--package-path iOS/Feature --mode implement\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report) == []

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "rtk python3 workflow/scripts/tool.py --reason Tests --state were "
            "--result not --mode run --cause simulator --detail unavailable\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Итог\n\n"
            "Задача реализует проверенный контракт авторизации.\n\n"
            "## Технические доказательства\n\n"
            "rtk python3 workflow/scripts/tool.py "
            "--tests-were-not-run-because-simulator-unavailable "
            "--known-limitations-remain-unresolved\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        authored_headings = (
            "Focused checks",
            "Фокусированные проверки",
            "Выполненные проверки",
            "Созданные файлы",
            "Созданные и изменённые файлы",
            "Изменённые файлы",
            "Изменённые task paths",
            "Изменённые production paths",
            "Изменённые test paths",
            "Unknown notes",
            "Ограничения",
        )
        for heading in authored_headings:
            report.write_text(
                "# task-001\n\n## Итог\n\n"
                "Задача реализует проверенный контракт авторизации.\n\n"
                f"## {heading}\n\n"
                "Tests were not run. Known limitation remains.\n",
                encoding="utf-8",
            )
            assert validate_task_evidence_language(repo, package, report), heading

        report.write_text(
            "# task-001\n\n## Технические доказательства\n\n"
            "very/long/path/AuthAPIClient.swift — English technical annotation\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        report.write_text(
            "# task-001\n\n## Итог\n\n```text\n"
            "Русский текст находится только внутри code fence.\n```\n",
            encoding="utf-8",
        )
        assert validate_task_evidence_language(repo, package, report)

        reconciliation = evidence / "reconciliation-20260716T120000Z-task-001.md"
        reconciliation.write_text(
            "## Итог\n\nРусский итог присутствует.\n\n## Changed paths\n\n"
            "This reconciliation annotation remains authored English prose.\n",
            encoding="utf-8",
        )
        assert validate_authored_markdown_language(repo, package, reconciliation)

        directory_report = evidence / "task-002.md"
        directory_report.mkdir()
        assert validate_task_evidence_language(repo, package, directory_report)
        invalid_utf8 = evidence / "task-003.md"
        invalid_utf8.write_bytes(b"\xff\xfeinvalid task evidence")
        assert validate_task_evidence_language(repo, package, invalid_utf8)
        linked_report = evidence / "task-004.md"
        linked_report.symlink_to(report.name)
        assert validate_task_evidence_language(repo, package, linked_report)

    print(
        "artifact-language self-test: PASS "
        "(sentence isolation, line-classified task evidence, bounded commands, JSON prose)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
