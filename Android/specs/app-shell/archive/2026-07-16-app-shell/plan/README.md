# Plan — app shell / Android / app-shell

## Planning frame

Реализовать утверждённую product-backed Android shell как небольшую
изолированную Gradle Android library capability. Текущий `:app` module
остаётся владельцем запуска и композиции; новая capability владеет метаданными
направлений, состоянием выбора, Material 3 navigation UI, локализованными
подписями и focused tests. Сеть, хранение, аналитика, permissions,
DI framework и product content не вводятся.

## Revalidated engineering scopes and exact rules

Финальные sealed engineering scopes: `["application", "compose", "gradle",
"localization", "module", "ui"]`. Выбор повторно проверен по current
repository evidence: `Android/settings.gradle.kts` содержит только `:app`,
`Android/app/build.gradle.kts` уже включает Compose и Material 3, shared
product contract имеет `READY`/`APPROVED`, а `platform-ux.md` имеет `READY`.
Русское уточнение: выбранные области подтверждены текущими файлами проекта и
утверждённым продуктовым контрактом.

Точный набор plan rules зафиксирован в `plan/rule-selection.json` и отражён в
`meta.json`. После этого плана downstream implementation и verification не
добавляют новые области работы.

## DAG

`task-001` не имеет dependencies и создаёт physical library boundary.
`task-002` зависит от `task-001` и создаёт public state contract с module-level
unit tests. `task-003` зависит от `task-002` и реализует Material 3 UI,
resource labels и Compose scenarios. `task-004` зависит от `task-003` и
подключает `:app` к public seam через consumer build и runtime verification
paths. Каждый шаг сохраняет русскоязычное описание цели, границы и проверки.
Русское уточнение: граф задач остаётся последовательным, понятным и пригодным
для поэтапной реализации без скрытых зависимостей.

## Tasks

`task-001` покрывает включение Gradle project, module build wiring,
dependency graph shape и начальный public API placeholder для downstream tests.
`task-002` покрывает deterministic selection state и contract tests.
`task-003` покрывает native UI, localization resources, accessibility
semantics, design-system checks, light/dark appearance и soft-blue fallback
decisions из `platform-ux.md`. `task-004` покрывает root composition,
app-shell wiring, consumer integration и final focused verification commands.
Русское уточнение: каждая задача имеет собственную ответственность и вместе
они покрывают сборку, состояние, интерфейс, ресурсы и интеграцию.
Дополнительное русское уточнение: такой набор задач позволяет двигаться
последовательно, не смешивая модульную границу, состояние, визуальный слой и
потребление из приложения.

## Estimates and multipliers

Каждая задача ограничена двумя ideal days. Главная неопределённость — greenfield
Android library wiring на AGP 9.2.1 и доступность emulator для runtime
evidence. Если emulator недоступен, runtime-only checks остаются `UNKNOWN` во
время Verify, а не выводятся из static tests.

## Verification strategy

Для каждого observable contract применяется TDD: сначала focused failing unit
или Compose scenario, затем минимальное behavior, затем narrow task command
через `workflow/scripts/test-watchdog.sh`. Уже обнаруженные Gradle tasks:
`app:testDebugUnitTest`, `app:lintDebug`, `app:assembleDebug`,
`app:connectedDebugAndroidTest` и `app:check`. Будущие `:app-shell:*` commands
остаются provisional, пока `task-001` не материализует module и Gradle task
discovery не будет обновлён.

## Test and performance budgets

Unit и Compose test commands используют max 300 seconds, stall 60 seconds,
output 1200 lines. Consumer build и lint commands используют max 420 seconds,
stall 90 seconds, output 2000 lines. Connected runtime checks используют max
600 seconds, stall 120 seconds, output 2500 lines и требуют discovered emulator
или device. Заявление о производительности продукта в этом increment не
делается.
Русское уточнение: бюджеты конечны, чтобы проверки не зависали и давали
понятный результат.
Дополнительное русское уточнение: ограничения времени и вывода нужны для
повторяемой проверки, а не для заявления о скорости продукта.

## Checkpoints

Перед staging нужно выполнить reconcile для explicit production path set этого
Android package. Commit допустим только после staged pre-commit integrity.
Production code намеренно не пишется в фазе Plan.
Русское уточнение: этот документ остаётся планом работ и не разрешает
самостоятельное расширение набора файлов.
