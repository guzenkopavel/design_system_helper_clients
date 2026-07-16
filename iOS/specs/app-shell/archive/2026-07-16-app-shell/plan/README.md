# Plan — app-shell / iOS / app-shell

## Planning frame

План переводит валидный package из `specified` в `planned` без изменения
production-кода. Реализация должна заменить технический Core Data root на
локальную оболочку приложения, сохранить ответственность application target в
allowlist и дать проверяемую нативную UI-поверхность для трёх направлений.

## Revalidated engineering scopes and exact rules

- Selection snapshot: `plan/rule-selection.json`
- Engineering scopes: `["application", "ui"]`
- Selection evidence: `application` остаётся выбранным, потому что изменение
  начинается в `SysDevScenApp.swift` и root composition; `ui` остаётся выбранным,
  потому что `ContentView.swift` является текущей SwiftUI-поверхностью и будет
  заменён нативным app shell. Новые `package`, `data`, `networking`,
  `localization` и performance scopes не добавлены: boundary guard оставил
  `not-applicable`, данных и отдельной возможности нет.

Точный список файлов правил:

- `workflow/rules/coding-standards.md`
- `workflow/rules/artifact-language.md`
- `workflow/rules/tdd-first.md`
- `workflow/rules/test-execution.md`
- `workflow/rules/verification-matrix.md`
- `workflow/rules/system-design/modularity.md`
- `iOS/workflow/rules/architecture.md`
- `iOS/workflow/rules/package-development.md`
- `iOS/workflow/rules/app-development.md`
- `iOS/workflow/rules/ios-pitfalls.md`
- `iOS/workflow/rules/architecture/feature-first.md`
- `iOS/workflow/rules/architecture/dependency-injection.md`
- `iOS/workflow/rules/architecture/use-cases.md`
- `iOS/workflow/rules/architecture/error-handling.md`
- `iOS/workflow/rules/architecture/naming.md`
- `iOS/workflow/rules/architecture/legacy.md`
- `iOS/workflow/rules/architecture/types-clean-code.md`
- `iOS/workflow/rules/unit-testing.md`
- `iOS/workflow/rules/accessibility.md`
- `iOS/workflow/rules/ui-design-system.md`
- `iOS/workflow/rules/ui-testing.md`
- `iOS/workflow/rules/ui-test-spec.md`
- `iOS/workflow/rules/simulator.md`
- `iOS/workflow/rules/architecture/mvvm.md`

## Assumptions

Команда реализации будет работать в текущем Xcode project `SysDevScen` со
scheme `SysDevScen`, targets `SysDevScen`, `SysDevScenTests` и
`SysDevScenUITests`. Доступный simulator runtime: iOS 26.5; обнаруженный
destination для команд: `platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5`.

## DAG

`task-001` создаёт application boundary и убирает техническую Core Data
composition из root path. `task-002` зависит от `task-001` и реализует нативную
UI-поверхность app shell. `task-003` зависит от `task-001` и `task-002` и
закрывает focused unit/UI/evidence проверки. Граф: `task-001` -> `task-002` ->
`task-003`, при этом `task-003` также явно проверяет результат `task-001`.

## Tasks

- `task-001`: корневая композиция и проверка `application boundary`.
- `task-002`: нативная SwiftUI shell-поверхность и UX adapter checks.
- `task-003`: сфокусированные тесты, проверки simulator и маппинг evidence.

## Estimates and multipliers

Оценки учитывают маленький app-shell scope, существующий технический шаблон
Core Data и необходимость accessibility/UI evidence. Каждая задача меньше двух
ideal days: `task-001` — 0.5-1.0 days, `task-002` — 1.0-1.5 days,
`task-003` — 1.0-2.0 days.

## Verification strategy

Сначала проверяется владение и `application boundary`, затем нативная UI
семантика, затем тесты и evidence. Минимальный terminal набор для implementation:
build, unit/UI test на discovered simulator destination, статический review
корневого пути и ручная запись evidence для всех строк `verification.md`.

## Test and performance budgets

Команда сборки:

```bash
xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
```

Команда тестов:

```bash
xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' test
```

Watchdog budgets: для build/test задано max 900s, stall 120s, output 20MB.
Для UI flow задано max 1200s, stall 180s, output 30MB. Этот change не выбирает
performance scope, но UI task обязан не добавлять лишнюю стоимость отрисовки из
`platform-ux.md`.

## Checkpoints

- После `task-001`: корневой путь больше не несёт Core Data context injection в
  app shell, а `application boundary` остаётся в allowlist.
- После `task-002`: видны «Кейсы», «Знания», «Профиль», начальный выбор
  «Кейсы» и ровно один selected state.
- После `task-003`: все `REQ`, `AC`, `IOS-REQ` и `IOS-AC` имеют маршрут от
  pending к evidence и сфокусированный command output.

## Risks

Основной риск — случайно оставить шаблонные Core Data interactions в root path
или выразить selected state только цветом. Второй риск — использовать Liquid
Glass API без проверки availability; для него обязателен older-OS/SDK fallback.
