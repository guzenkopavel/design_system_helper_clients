# task-001 — Создать Android library boundary

- Layer: infrastructure
- Boundary owner: Владелец Gradle Android library boundary и project graph для app shell
- Engineering scopes: ["gradle", "module"]
- Depends on: none
- Status: done
- Evidence: evidence/reconciliation-20260716T120500Z-task-001-android-aligned.md
- Discovered command: rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 1200 -- ./Android/gradlew -p Android --no-daemon :app-shell:assembleDebug --console=plain
- Estimate (ideal): 0.5–1 days
- Paths: existing: Android/settings.gradle.kts; existing: Android/build.gradle.kts; existing: Android/gradle/libs.versions.toml; proposed: Android/app-shell/build.gradle.kts; proposed: Android/app-shell/src/main/AndroidManifest.xml

## Goal

Создать изолированный Gradle Android library module для возможности app shell,
подключить его к обнаруженному графу проекта и сохранить `:app` в роли
только композиции.

## Inline contract context

`AND-REQ-1` требует, чтобы UI оболочки, состояние выбора, подписи и
нейтральные поверхности жили за Android library boundary. `AND-AC-1` требует
собираемую границу и одностороннюю композицию; shared `REQ-1` и `AC-1` требуют
ровно три видимых направления в утверждённом порядке.

## Steps

Добавить include `:app-shell` в `Android/settings.gradle.kts`, создать Gradle
Android library build file только на обнаруженных catalog aliases и добавить
минимальный manifest/source-set layout. Держать module boundary явным: наружу
виден только minimal public contract, `:app` не владеет состоянием возможности,
а dependency graph остаётся acyclic. После появления модуля обновить Gradle
task discovery и записать новые имена задач сборки модуля перед
использованием. Сохранить app-shell wiring как ответственность consumer в
`:app`, а не как бизнес-поведение внутри application module.

## Verification

Сначала выполнить RED diagnostic, показывающий отсутствие `:app-shell` в
`./Android/gradlew -p Android projects --console=plain`; после wiring запустить
`rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300
--stall-seconds 60 --max-output-lines 1200 -- ./Android/gradlew -p Android
projects --console=plain` и подтвердить наличие `:app-shell`. Затем запустить
обнаруженную или обновлённую Gradle task для module build; provisional command:
`./Android/gradlew -p Android :app-shell:assembleDebug --console=plain`.
Доказательства должны явно содержать markers Gradle task, module boundary,
module build, public contract, consumer integration, dependency graph и
app-shell wiring; эти английские маркеры оставлены только как точные checks
для валидатора.

## Expected result

Граф проекта содержит buildable isolated library module, dependency cycle не
появляется, а `:app` готов потреблять public app-shell contract.
Русское уточнение: ожидаемый результат фиксирует собираемую границу, понятное
направление зависимости и отсутствие переноса логики в приложение.

## Out of scope

Поведение направлений, Material 3 UI, runtime screen wiring, emulator claim и
несвязанный Gradle cleanup в эту задачу не входят.
