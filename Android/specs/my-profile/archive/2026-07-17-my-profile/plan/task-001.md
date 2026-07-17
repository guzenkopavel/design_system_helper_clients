# task-001 — Создать границу сборки профиля

- Layer: infrastructure
- Boundary owner: Владелец библиотечной границы сборки для возможности профиля
- Engineering scopes: ["gradle","module"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Estimate (ideal): 0.5-1 days
- Read-only context: ["Android/app-shell/build.gradle.kts","Android/auth/build.gradle.kts","Android/gradle/libs.versions.toml","Android/specs/my-profile/changes/my-profile/design.md","Android/specs/my-profile/changes/my-profile/implementation-spec.md"]
- Paths: existing: Android/settings.gradle.kts; proposed: Android/my-profile/build.gradle.kts; proposed: Android/my-profile/src/main/AndroidManifest.xml; proposed: Android/my-profile/src/main/java/ru/home/sysdevsc/myprofile/ProfileRoute.kt; proposed: Android/my-profile/src/main/java/ru/home/sysdevsc/myprofile/ProfileState.kt; proposed: Android/my-profile/src/test/java/ru/home/sysdevsc/myprofile/ProfileContractTest.kt

## Goal

Создать физическую библиотечную единицу `:my-profile` с минимальным публичным `Compose`-контрактом и начальными контрактными проверками, чтобы возможность профиля получила собственную границу модуля до появления данных, интерфейса и корневого связывания.

## Inline contract context

`AND-REQ-1` требует отдельную библиотечную единицу с минимальным публичным `Compose`-контрактом. `AND-AC-1` требует, чтобы граф сборки включал отдельную библиотечную единицу профиля, а `:app` зависел от публичного контракта без владения логикой профиля.

## Implementation deliverables

- Появится самостоятельный библиотечный модуль `:my-profile` с manifest, build file и минимальными публичными contract types профиля, которые собираются отдельно и не раскрывают внутренние детали данных или интерфейса потребителям.
- Начальная контрактная проверка подтвердит видимость публичного шва профиля и направление зависимости, а `dependency graph` останется ацикличным без переноса состояния профиля или сетевого владения в application shell.

## Steps

Добавить `include(":my-profile")` в обнаруженный `Android/settings.gradle.kts`. Создать `Android/my-profile/build.gradle.kts` на существующих alias каталога для библиотеки Android, `Compose`, `Material 3`, lifecycle, coroutines, `OkHttp`, `Moshi` и test dependencies без добавления `Hilt` или неподтверждённых plugins. Создать manifest и минимальные `ProfileRoute` / `ProfileState` placeholders только как `public contract seam`. Добавить сфокусированную контрактную проверку, которая сначала падает из-за отсутствующей границы, затем подтверждает `public contract` и `Gradle task` discovery.

## Verification

- Discovered command: `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 1200 -- ./gradlew projects --console=plain`
- Watchdog max/stall/output budget for nontrivial checks: `300s / 60s / 1200 lines` для Gradle project discovery; `420s / 90s / 2000 lines` для `:my-profile:assembleDebug` после materialization.
- Applicable rule/check mapping: проверить `Gradle task`, `module boundary`, `module build`, `public contract`, `consumer integration`, `dependency graph` и `app-shell wiring`; в этой задаче `consumer integration` означает готовность публичного контракта к подключению без зависимости от `:app-shell`.

## Expected result

Граф проекта показывает `:my-profile`, задача сборки модуля обнаружена, публичный контракт компилируется, контрактная проверка фиксирует направление границы, а application shell остаётся без владения возможностью профиля. Команды `:my-profile:*` становятся подтверждёнными для последующих задач.

## Out of scope

Реализация репозитория, сетевые запросы, пагинация, поведение выхода, полноценный экран `Compose`, слот содержимого оболочки, корневое восстановление авторизации и проверки runtime-эмулятора в эту задачу не входят.
