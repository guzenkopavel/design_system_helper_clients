# task-003 — focused tests и evidence mapping

- Layer: tests
- Boundary owner: app-shell verification boundary across unit and UI test targets
- Engineering scopes: ["application", "ui"]
- Depends on: task-001, task-002
- Status: done
- Evidence: evidence/task-003.md
- Estimate (ideal): 1.0-2.0 days
- Paths: existing: iOS/SysDevScen/SysDevScenTests; existing: iOS/SysDevScen/SysDevScenUITests; proposed: iOS/SysDevScen/SysDevScenTests/AppShellStateTests.swift; proposed: iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift

## Goal

Добавить сфокусированные unit/UI проверки и evidence route для всех shared и
iOS contracts, не расширяя scopes и не добавляя production behavior вне
approved app shell.

## Inline contract context

Покрывает `REQ-1`, `REQ-2`, `REQ-3`, `REQ-4`, `REQ-5`, `REQ-6`, `AC-1`, `AC-2`,
`AC-3`, `AC-4`, `AC-5`, `IOS-REQ-1`, `IOS-REQ-2`, `IOS-REQ-3`, `IOS-AC-1`,
`IOS-AC-2` и `IOS-AC-3`. Задача отвечает за командную проверку, simulator
evidence, `application boundary` и UI accessibility checks.
`verification.md` и package `evidence/` используются как read-only context и
route для отчёта; initial Implement пишет только точные разрешённые файлы
`evidence/task-003.md` и `evidence/scope-baseline-task-003.json`.

## Steps

- Добавить `deterministic unit tests` для начального раздела, каждого выбора,
  повторного выбора, идемпотентности и закрытого набора `RootSection`.
- Добавить `UI tests` для запуска, трёх labels, переноса selected state,
  отсутствия Core Data template interactions и постоянной navigation.
- Подготовить сопоставление строк `verification.md` с evidence route через
  `evidence/task-003.md`; сам `verification.md` остаётся read-only до
  отдельной Verify-фазы.
- Проверить `application boundary`, отсутствие нового package/target,
  отсутствие data/network/persistence ownership и отсутствие excluded template
  behavior.
- Выполнить UI checks: `simulator`, `accessibility`, `design-system`,
  `platform-ux.md`, `Liquid Glass`, `light/dark`, `increased contrast`,
  `Reduce Transparency`, `Reduce Motion` и `older-OS/SDK fallback`.

## Verification

- Discovered command: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' test`
- Watchdog max/stall/output budget for nontrivial checks: test max 900s, stall 120s, output 20MB; UI flow max 1200s, stall 180s, output 30MB.
- Applicable rule/check mapping: TDD first, verification matrix, `application boundary`,
  `simulator`, `accessibility`, `design-system`, `platform-ux.md`, `Liquid Glass`,
  `light/dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion`,
  `older-OS/SDK fallback`.

## Expected result

Команда `xcodebuild test` проходит на обнаруженном destination. Тесты покрывают
все contract IDs из контекста задачи, маршрут evidence готов для Verify, а
package остаётся в sealed scopes `application` и `ui`.

## Out of scope

Бенчмарки производительности, файлы локализации, события аналитики, реальный
контент разделов, network/data mocks, package extraction и commit остаются вне
этой задачи.
