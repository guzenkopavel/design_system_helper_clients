# task-004 — Подключить шов оболочки и корневую композицию

- Layer: infrastructure
- Boundary owner: Владелец границы приложения и композиционного шва оболочки
- Engineering scopes: ["application","module"]
- Depends on: task-003
- Status: done
- Evidence: evidence/task-004.md
- Estimate (ideal): 1-2 days
- Read-only context: ["Android/specs/app-shell/SPECIFICATION.md","Android/specs/my-profile/changes/my-profile/design.md","Android/specs/my-profile/changes/my-profile/implementation-spec.md","Android/specs/user-profile-auth/SPECIFICATION.md"]
- Paths: existing: Android/app/build.gradle.kts; existing: Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt; existing: Android/app-shell/build.gradle.kts; existing: Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShell.kt; proposed: Android/app/src/androidTest/java/ru/home/sysdevsc/MyProfileIntegrationTest.kt; proposed: Android/app-shell/src/test/java/ru/home/sysdevsc/appshell/ProfileContentSlotTest.kt

## Goal

Подключить содержимое профиля через публичный слот оболочки и корневую композицию, сохранив `:app` как composition-only boundary и `:app-shell` как навигационную рамку без владения данными профиля.

## Inline contract context

`AND-REQ-2` требует, чтобы destination профиля показывал содержимое профиля через content slot или эквивалентный публичный шов без переноса логики в `:app-shell`. `AND-REQ-7` и `AND-REQ-10` требуют callback выхода и восстановление недействительной сессии через корневой auth gate. `AND-AC-2`, `AND-AC-8`, `AND-AC-9` и `AND-AC-10` проверяют шов содержимого оболочки, маршрутизацию успешного выхода, восстановление сбоя выхода и очистку недействительной сессии.

## Implementation deliverables

- `:app-shell` получит минимальный слот содержимого профиля, который сохраняет подписи нижней навигации, выбранное состояние и базовое поведение оболочки без владения репозиторием профиля, состоянием или сетевой логикой.
- `:app` подключит `:my-profile` как `consumer integration`, передаст зависимости и обратные вызовы для выхода или недействительной сессии, а auth gate после успешного выхода вернётся к пустому вводу почты без персональных данных прошлого профиля.

## Steps

Расширить публичный контракт `AppShell` так, чтобы направление профиля могло принимать content lambda или typed slot, не меняя остальные направления. Добавить dependency `implementation(project(":my-profile"))` в `:app`, связать profile route в `MainActivity` с auth/session callbacks и состоянием очистки. Написать проверки для рендера слота, выбранной нижней навигации, feedback без навигации, успешного выхода, сбоя выхода и восстановления недействительной сессии. Проверить `application boundary`, `module boundary`, `module build`, `public contract`, `consumer integration`, `dependency graph` и `app-shell wiring`; не переносить репозиторий или изменяемое состояние профиля в `:app` или `:app-shell`.

## Verification

- Discovered command: `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 2000 -- ./gradlew :app:assembleDebug :app-shell:testDebugUnitTest :app:testDebugUnitTest --console=plain`
- Watchdog max/stall/output budget for nontrivial checks: `420s / 90s / 2000 lines` для build/unit integration; `600s / 120s / 2500 lines` для app connected tests при runtime availability.
- Applicable rule/check mapping: проверить `application boundary`, `module boundary`, `module build`, `public contract`, `consumer integration`, `dependency graph` и `app-shell wiring` через tests, вывод зависимостей Gradle или сфокусированное build evidence.

## Expected result

Destination профиля показывает реальное содержимое профиля через шов оболочки, нижняя навигация остаётся совместимой с baseline, `:app` компонует зависимости и callbacks, выход или недействительная сессия очищают отображение профиля и возвращают auth flow без расширения владения оболочки.

## Out of scope

Изменение общего продуктового контракта, backend API, внутренних деталей авторизации за пределами публичного шва, новый экран истории, аналитика и несвязанный redesign оболочки не входят в эту задачу.
