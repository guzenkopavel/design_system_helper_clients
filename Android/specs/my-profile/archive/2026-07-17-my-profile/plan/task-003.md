# task-003 — Создать Compose UI профиля

- Layer: presentation
- Boundary owner: Владелец представления Compose и ресурсов внутри возможности профиля
- Engineering scopes: ["compose","localization","ui"]
- Depends on: task-002
- Status: done
- Evidence: evidence/task-003.md
- Estimate (ideal): 1-2 days
- Read-only context: ["Android/specs/my-profile/changes/my-profile/platform-ux.md","Android/specs/my-profile/changes/my-profile/verification.md","specs/product/my-profile/spec.md"]
- Paths: proposed: Android/my-profile/src/main/java/ru/home/sysdevsc/myprofile/ui; proposed: Android/my-profile/src/main/res/values/strings.xml; proposed: Android/my-profile/src/androidTest/java/ru/home/sysdevsc/myprofile/ui

## Goal

Сделать экран профиля на `Material 3` и `Compose` с крупным стандартным символом аккаунта, почтой, действиями «Мои интервью» и «Выход», восстановимыми состояниями, русскими ресурсами, ассистивной семантикой и проверяемым `soft-blue fallback`.

## Inline contract context

`AND-REQ-5` требует видимое, но условно доступное действие «Мои интервью». `AND-REQ-6` требует краткую обратную связь «Интервью: N» без навигации. `AND-REQ-8` требует профильный экран на `Material 3`. `AND-REQ-11` и `AND-REQ-12` требуют наблюдаемый паритет, доступность, локализацию и адаптивный внешний вид. `AND-AC-3`, `AND-AC-5`, `AND-AC-6`, `AND-AC-7`, `AND-AC-11`, `AND-AC-12`, `AND-AC-13`, `AND-AC-14` и `AND-AC-15` задают проверяемое поведение интерфейса.

## Implementation deliverables

- Появится экран профиля `Compose` на `Material 3` и `MaterialTheme`, где почта, недоступное состояние, занятый выход, восстановимые сообщения и краткая обратная связь представлены через неизменяемое состояние и однонаправленные события.
- Ресурсы интерфейса и Compose tests подтвердят русскую `localization`, ассистивную семантику, использование `design-system`, проверки `platform-ux.md`, внешний вид `light/dark`, `accessible on-colors`, решение по `dynamic color` и `soft-blue fallback` без опоры только на цвет.

## Steps

Создать state holder или шов ViewModel, который отдаёт состояние `Compose` через lifecycle-aware collection и не удерживает `Activity`, `Context` или `Resources`. Реализовать интерфейс через компоненты `Material 3`, `MaterialTheme.colorScheme`, typography, shapes, semantic tonal roles и `accessible on-colors`. Добавить строковые ресурсы для «Мои интервью», «Выход», «Интервью: %d» и восстановимых сообщений. Написать Compose UI tests для готового счётчика, нулевого счётчика, неизвестного счётчика, ошибки истории, offline, занятого выхода, объявления feedback, события без навигации и разметки с безопасным увеличением текста. В steps реализации явно проверить `platform-ux.md`, `Material 3`, `light/dark`, `accessible on-colors`, решение доступности `dynamic color` и `soft-blue fallback`.

## Verification

- Discovered command: `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 2500 -- ./gradlew :my-profile:connectedDebugAndroidTest --console=plain`
- Watchdog max/stall/output budget for nontrivial checks: `600s / 120s / 2500 lines` для runtime UI; `300s / 60s / 1200 lines` для local state tests; runtime-команда предварительная до подтверждения эмулятора или устройства.
- Applicable rule/check mapping: `Compose state`, `localization`, `emulator`, `accessibility`, `design-system`, `platform-ux.md`, `Material 3`, `light/dark`, `accessible on-colors`, `dynamic color` и `soft-blue fallback` должны появиться в evidence как отдельные checks.

## Expected result

Пользовательский профиль визуально и ассистивно показывает почту, состояния истории, доступное или недоступное действие, feedback «Интервью: N» и процесс выхода; runtime или bounded `UNKNOWN` фиксирует результат `emulator`, `accessibility` и `design-system` без подмены unit-покрытием.

## Out of scope

Внутренности сетевого репозитория, настройки Gradle, изменение API оболочки, связывание `MainActivity`, изменения хранилища авторизации, экран списка интервью и `M3 Expressive` без evidence от repository SDK/dependency/product не входят в эту задачу.
