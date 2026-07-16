# task-004 — Подключить app composition и final focused checks

- Layer: presentation
- Boundary owner: Владелец Android application composition root и consumer integration
- Engineering scopes: ["application", "compose", "gradle", "module", "ui"]
- Depends on: task-003
- Status: pending
- Evidence: none
- Estimate (ideal): 0.5–1.5 days
- Paths: existing: Android/app/build.gradle.kts; existing: Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt; existing: Android/app/src/main/AndroidManifest.xml; proposed: Android/app/src/androidTest/java/ru/home/sysdevsc/AppShellIntegrationTest.kt

## Goal

Подключить существующую Android entry point к public seam app-shell, сохранив
`:app` ограниченным lifecycle, root composition, target resources и consumer
integration. Описанная ответственность остаётся русскоязычной, а английские
термины здесь обозначают точные технические границы.

## Inline contract context

`REQ-1`, `REQ-2`, `REQ-3`, `AC-1`, `AC-2` и `AC-3` требуют, чтобы launch
показывал три направления, initial selection `Кейсы` и observable transitions.
`AND-REQ-1`, `AND-AC-1` и `AND-AC-2` требуют buildable app composition через
isolated public boundary.
Русское уточнение: запуск приложения должен использовать готовую публичную
границу, а не владеть состоянием возможности.

## Steps

Добавить только project dependency, нужную `:app` для composition library seam,
заменить template greeting в `MainActivity` и сохранить владение состоянием
внутри app-shell module. Compose state используется через public seam, а
application boundary responsibility ограничивается lifecycle/root composition.
Затем снова запустить Gradle task discovery и доказать module boundary,
module build, public contract, consumer integration, dependency graph и
app-shell wiring. Для UI coverage включить emulator, accessibility,
design-system, platform-ux.md, Material 3, light/dark, accessible on-colors,
dynamic color exclusion и soft-blue fallback checks там, где runtime это
позволяет.
Русское уточнение: приложение выполняет роль потребителя и композиционного
корня, сохраняя логику в отдельном модуле.
Дополнительное русское уточнение: изменение не должно превращать `:app` во
владельца поведения, состояния или визуальной логики оболочки.

## Verification

Запустить consumer build и focused test set под watchdog:
`rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420
--stall-seconds 90 --max-output-lines 2000 -- ./Android/gradlew -p Android
app:assembleDebug app:testDebugUnitTest app:lintDebug --console=plain`.
Если runtime обнаружен, запустить `rtk bash
workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120
--max-output-lines 2500 -- ./Android/gradlew -p Android
app:connectedDebugAndroidTest --console=plain`. Evidence должен явно связать
application boundary, Gradle task, Compose state, emulator availability,
accessibility, design-system, module boundary, module build, public contract,
consumer integration, dependency graph и app-shell wiring checks; это набор
точных markers для валидатора.
Русское уточнение: evidence должен показать сборку потребителя, направление
зависимостей и доступность проверок.
Дополнительное русское уточнение: проверка нужна для уверенности, что
приложение только компонует публичный контракт и не нарушает модульность.

## Expected result

Launch через `:app` компонует isolated app-shell UI, consumer build проходит,
а final focused checks могут поддержать каждую pending Android и shared
verification row.
Русское уточнение: итог задачи готовит пакет к последующим проверкам, но сам
не выставляет terminal verification status.

## Out of scope

Новые product surfaces, cross-platform implementation, data layer,
persistence, permission, analytics, release signing и commit operation в эту
задачу не входят.
Русское уточнение: задача не расширяет продукт, не трогает выпуск и не делает
операций Git.
Дополнительное русское уточнение: область задачи ограничена подключением
оболочки и focused checks без новых функций и внешних действий.
