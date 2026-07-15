---
phase: harness-review
writes_artifacts: []
requires_verification: true
recommended_roles:
  - harness-auditor
  - implementation-writer
---

# Phase: Harness Review

Проверять сам харнес, а не продуктовый код. Совмещать детерминированный lint и
read-only аудит смысловой согласованности.

## Процедура

1. Запустить `python3 workflow/scripts/harness-lint.py` или вариант `--json`.
2. Передать scope и вывод линтера роли `harness-auditor`.
3. Свести результаты в один список: critical → warning → judgment → info.
4. Передать подтверждённые исправления `implementation-writer`.
5. Повторять lint и аудит до grade A + `CLEAN`.

## Что проверяет линтер

- битые относительные Markdown-ссылки;
- frontmatter и имя skill относительно каталога;
- наличие канонической phase у skill-shim;
- валидность TOML и уникальность runtime-ролей;
- parity ролей и skill entry points для Codex/Claude Code/Cursor/OpenCode;
- dead dispatch references на роли;
- наличие iOS/Android scope-контракта;
- нейминг harness-файлов.

## Что проверяет аудитор

- дубли и нарушения SSOT;
- логические противоречия;
- смысловой parity канон↔адаптер;
- dead prose references;
- точность agent roster и process map;
- корректность common/ios/android/cross-platform placement.

Для `cross-platform` вынести iOS и Android в отдельные секции отчёта.
Ревью-роли не изменяют файлы. Не создавать коммит без явной просьбы.

Способ вызова auditor выбирать по
[`../rules/runtime-adapters.md`](../rules/runtime-adapters.md).
