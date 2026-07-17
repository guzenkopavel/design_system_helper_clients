# iOS UI runner recovery — harness change evidence

## Change plan

- **Тип:** rule
- **Операция:** modify
- **Зачем:** в verification-сессии `xcodebuild test -only-testing:SysDevScenUITests`
  дважды молчал до полезного output/зависал на runner preparation. Процесс уже
  запрещал превращать retry в PASS, но не описывал безопасный iOS recovery path:
  зафиксировать runner UNKNOWN, отключить parallel testing и закрыть ту же
  method matrix focused suites.
- **Scope:** ios

## Locate

- **Затронутый flow:** platform implementation lifecycle → verify → UI/runtime checks.
- **Канонический владелец:** `iOS/workflow/rules/ui-testing.md`.
- **Placement:** adapter · ios.
- **SSOT-проверка:** общие `workflow/rules/test-execution.md` и
  `iOS/workflow/rules/simulator.md` уже владеют watchdog/stall и simulator
  isolation; дубль не создан, добавлена только iOS-specific recovery policy для
  Xcode UI automation.
- **Просмотрено:** `.agents/skills/harness-change/SKILL.md`,
  `.agents/skills/harness-review/SKILL.md`, `workflow/phases/harness-change.md`,
  `workflow/templates/harness-change.md`, `process/README.md`,
  `process/entities.md`, `process/flows.md`,
  `workflow/rules/test-execution.md`, `iOS/workflow/rules/simulator.md`,
  `iOS/workflow/rules/ui-testing.md`.

## Forbidden

- **Зависимости:** iOS plan/implement/verify UI tasks, simulator evidence и
  terminal verification reports.
- **Инварианты:** single-writer, no-commit, SSOT, platform isolation, finite
  watchdog budgets, retry does not erase failure, чужие simulator resources не
  удаляются.

## Root documentation impact

- **README.md:** no-impact — entrypoints и capability overview не меняются.
- **workflow.md:** no-impact — operational lifecycle route не меняется; правило
  уточняет только iOS UI runner recovery внутри platform rule.
- **deep-info.md:** update/generated — inventory может обновиться после render
  из-за изменения iOS rule и нового test evidence.

## Verification notes

Ожидаемые проверки после изменения:

- `rtk python3 workflow/scripts/harness-docs.py render`
- `rtk python3 workflow/scripts/harness-docs.py check --json`
- `rtk python3 workflow/scripts/harness-lint.py --json`
