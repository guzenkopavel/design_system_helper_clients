# task-004 — доказательства

## Итог

Задача выполнена. Модуль `:app` подключён как потребитель `:app-shell` через
Gradle dependency и теперь компонует публичную оболочку приложения в
`MainActivity`. Application boundary остаётся ограниченной entry point,
lifecycle и root composition: состояние выбора создаётся через публичный
`AppShellState`, а переходы выполняются через `AppShellState.select(...)`.

## RED

Команда:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 1800 -- ./Android/gradlew -p Android --no-daemon :app:connectedDebugAndroidTest --console=plain
```

Результат: `BUILD FAILED`. Тест `AppShellIntegrationTest` дошёл до эмулятора
`Pixel_6(AVD) - 16` и упал на отсутствии текста `Кейсы`, потому что launch ещё
показывал template greeting вместо app-shell.

## GREEN

Команда сборки потребителя, unit tests и lint:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 2000 -- ./Android/gradlew -p Android --no-daemon app:assembleDebug app:testDebugUnitTest app:lintDebug --console=plain
```

Результат: `BUILD SUCCESSFUL`.

Команда runtime integration на эмуляторе:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 2500 -- ./Android/gradlew -p Android --no-daemon app:connectedDebugAndroidTest --console=plain
```

Результат: `BUILD SUCCESSFUL`. На `Pixel_6(AVD) - 16` выполнены 3 теста:
launch показывает `Кейсы`, `Знания`, `Профиль`, initial selection имеет
описание `Выбрано`, а переход на `Профиль` показывает нейтральную поверхность
этого направления.

Команда установки и ручного открытия:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 1000 -- ./Android/gradlew -p Android --no-daemon app:installDebug --console=plain
adb shell am start -n ru.home.sysdevsc/.MainActivity
```

Результат: `BUILD SUCCESSFUL`; APK установлен на `Pixel_6(AVD) - 16`, activity
открыта. Скриншот runtime: `/tmp/android-app-shell-task-004-20260716-115133.png`.

## Проверенные контракты

- `application boundary`: `:app` содержит точку входа, lifecycle и корневую
  композицию, но не переносит в себя реализацию UI оболочки.
- `Gradle task`: `app:assembleDebug`, `app:testDebugUnitTest`,
  `app:lintDebug` и `app:connectedDebugAndroidTest` выполнены через finite
  watchdog.
- `Compose state`: `MainActivity` вызывает `SysDevScApp`, где состояние
  передаётся в `AppShell`, а события выбора возвращаются через callback.
- `emulator availability`: runtime доступен как `Pixel_6(AVD) - 16`, Android
  16/API 36.
- `accessibility`: интеграционный тест проверяет семантику выбранности через
  `stateDescription` со строкой `Выбрано`.
- `design-system`: запуск использует `AppShell`, построенный на Material 3,
  `MaterialTheme`, семантических цветовых ролях и запасном спокойном синем
  оформлении из модуля `:app-shell`.
- `module boundary`: production UI остаётся в `:app-shell`; `:app` зависит от
  него через `implementation(project(":app-shell"))`.
- `module build`: сборка `:app` подтягивает `:app-shell` и успешно проходит
  consumer build.
- `public contract`: потребитель использует только `AppShell`, `AppShellState`
  и публичный переход `select(...)`.
- `consumer integration`: `MainActivity` больше не показывает template greeting
  и запускает утверждённую оболочку.
- `dependency graph`: направление зависимости `:app -> :app-shell`; обратной
  зависимости от `:app-shell` к `:app` нет.
- `app-shell wiring`: приложение отвечает за root composition, а app-shell
  module отвечает за UI seam, Material 3 presentation и состояние выбора.
- `platform-ux.md`: runtime проверяет оболочку Material 3 с русскими labels,
  семантикой выбранности и запретом вымышленных состояний loading, error,
  account и data.
- `light/dark`, `accessible on-colors`, `dynamic color`, `soft-blue fallback`:
  визуальные решения остаются в `:app-shell`; consumer wiring их не переопределяет
  и не включает dynamic color.

## Граница изменений

Команда:

```text
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform android --feature app-shell --change app-shell --task task-004 --baseline Android/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-004.json --expected-sha256 coordinator-held-token
```

Результат: `Implementation scope: VALID (check)`.
