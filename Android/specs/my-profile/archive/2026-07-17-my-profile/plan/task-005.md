# task-005 — Закрыть сфокусированную проверку профиля

- Layer: tests
- Boundary owner: Владелец доказательств проверки для возможности профиля и графа потребителя
- Engineering scopes: ["application","compose","concurrency","gradle","localization","module","ui"]
- Depends on: task-004
- Status: done
- Evidence: evidence/task-005.md
- Estimate (ideal): 1-2 days
- Read-only context: ["Android/specs/my-profile/changes/my-profile/platform-ux.md","Android/specs/my-profile/changes/my-profile/verification.md","workflow/rules/verification-matrix.md"]
- Paths: proposed: Android/app/src/androidTest/java/ru/home/sysdevsc/MyProfileRuntimeTest.kt; proposed: Android/my-profile/src/androidTest/java/ru/home/sysdevsc/myprofile/ProfileAppearanceTest.kt; proposed: Android/my-profile/src/test/java/ru/home/sysdevsc/myprofile/ProfileVerificationMatrixTest.kt

## Goal

Собрать сфокусированный набор проверок для всех Android profile REQ/AC: граф модуля, репозиторий и состояние, семантика `Compose`, локализация, интеграция приложения, внешний вид `Material 3`, доступность, доступность среды выполнения и наблюдаемый кросс-клиентский паритет.

## Inline contract context

`AND-REQ-1`-`AND-REQ-12` и `AND-AC-1`-`AND-AC-15` должны получить сфокусированное доказательство. Особенно важны `AND-AC-4` для завершения пагинации, `AND-AC-7` для обратной связи без навигации, `AND-AC-8`-`AND-AC-10` для выхода и восстановления недействительной сессии, `AND-AC-11`-`AND-AC-14` для `Material 3`, ассистивной семантики, увеличения текста и локализации, а также `AND-AC-15` для наблюдаемого кросс-клиентского паритета.

## Implementation deliverables

- Появится набор проверок матрицы верификации, который связывает репозиторий, состояние `Compose`, интеграцию приложения и проверки границы сборки с каждым критерием профиля без расширения владения производственным кодом.
- Ограниченное доказательство `runtime` зафиксирует `emulator`, `accessibility`, `design-system`, `platform-ux.md`, `Material 3`, `light/dark`, `accessible on-colors`, решение по `dynamic color` и исходы `soft-blue fallback` честно как `PASS` или `UNKNOWN`.

## Steps

Запустить сфокусированные `unit`-проверки, `module build`, `lint`, `assemble`, `consumer integration` и подключённые UI-команды через конечный watchdog. Проверить обнаружение `Gradle task` после появления `:my-profile`. Сверить `module boundary`, `module build`, `public contract`, `consumer integration`, `dependency graph`, `app-shell wiring` и `application boundary`. Для интерфейса проверить `Compose state`, `localization`, `emulator`, `accessibility`, `design-system`, `platform-ux.md`, `Material 3`, `light/dark`, `accessible on-colors`, доступность `dynamic color` и запасного варианта, `soft-blue fallback`, `cancellation` и поведение жизненного цикла. Сформировать доказательство по правилам матрицы верификации без утверждения `PASS` при недоступной среде выполнения.

## Verification

- Discovered command: `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 2000 -- ./gradlew :my-profile:testDebugUnitTest :my-profile:lintDebug :my-profile:assembleDebug :app:testDebugUnitTest :app:assembleDebug --console=plain`
- Watchdog max/stall/output budget for nontrivial checks: `300s / 60s / 1200 lines` для узких tests, `420s / 90s / 2000 lines` для build/lint, `600s / 120s / 2500 lines` для connected runtime; бесконечные повторы и очистка кэша без полномочий запрещены.
- Applicable rule/check mapping: задача явно покрывает `application boundary`, `Compose state`, `cancellation`, `lifecycle`, `Gradle task`, `localization`, `module boundary`, `module build`, `public contract`, `consumer integration`, `dependency graph`, `app-shell wiring`, `emulator`, `accessibility`, `design-system`, `platform-ux.md`, `Material 3`, `light/dark`, `accessible on-colors`, `dynamic color` и `soft-blue fallback`.

## Expected result

Сфокусированные команды проверки создают ограниченное доказательство для каждого запланированного Android-контракта профиля, граф модуля остаётся изолированным, поведение профиля совпадает с общим наблюдаемым паритетом, а недоступный эмулятор или среда доступности записывается как `UNKNOWN`, а не выводится из статических тестов.

## Out of scope

Запись `evidence/task-NNN.md`, изменение статусов lifecycle verification, commit файлов, добавление backend fixtures, широкий performance profiling и несвязанные refactors авторизации или оболочки находятся вне этой задачи плана.
