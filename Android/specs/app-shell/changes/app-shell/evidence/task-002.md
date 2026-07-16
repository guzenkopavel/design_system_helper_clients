# task-002 — доказательства

## Итог

Задача выполнена. В `Android/app-shell` добавлен минимальный публичный контракт
состояния для трёх утверждённых направлений оболочки приложения:

- `AppShellDestination` содержит только `Кейсы`, `Знания`, `Профиль`;
- `AppShellState.initial()` выбирает `Кейсы`;
- `AppShellState.select(...)` детерминированно заменяет выбранное направление;
- повторный выбор текущего направления возвращает тот же неизменяемый объект
  состояния;
- держатель состояния не зависит от `Context`, `Resources`, Activity, владельца
  lifecycle, хранилища, сети, DI framework или Compose UI.

## RED

Команда:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 220 -- ./Android/gradlew -p Android --no-daemon :app-shell:testDebugUnitTest --console=plain
```

Результат: `BUILD FAILED`. Компиляция тестового исходника не нашла
`AppShellDestination` и `AppShellState`, что подтвердило отсутствие публичного
контракта состояния до реализации. Дополнительно проявилось, что зависимость
JUnit не входит в заявленный scope задачи для `app-shell`, поэтому финальная
узкая проверка выполнена без изменения Gradle build file.

## GREEN

Команда компиляции тестового исходника модуля:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 500 -- ./Android/gradlew -p Android --no-daemon :app-shell:compileDebugUnitTestKotlin --console=plain
```

Результат: `BUILD SUCCESSFUL`.

Команда исполнения узкой проверки контракта состояния:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 120 --stall-seconds 30 --max-output-lines 200 -- java -cp 'Android/app-shell/build/intermediates/built_in_kotlinc/debugUnitTest/compileDebugUnitTestKotlin/classes:Android/app-shell/build/intermediates/built_in_kotlinc/debug/compileDebugKotlin/classes:/Users/pavel/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.2.10/30de6faa127a4a012db8e71bf1b9c0a99b1402b2/kotlin-stdlib-2.2.10.jar:/Users/pavel/.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib-jdk8/2.2.10/80cc9a776a058eeda7053731350bc41af8858a5a/kotlin-stdlib-jdk8-2.2.10.jar' ru.home.sysdevsc.appshell.AppShellStateTestKt
```

Результат: exit code `0`. Проверены начальный выбор, повторный выбор текущего
направления, переход к каждому destination и исчерпывающий контракт без
четвёртого состояния.

## Доказательства границ

- `application boundary`: держатель состояния находится в `Android/app-shell` и
  не содержит Activity, Android lifecycle, DI, persistence, network или доступ к
  ресурсам.
- `module boundary`: публичный контракт представлен типизированным Kotlin API
  `AppShellDestination` и `AppShellState` внутри отдельного `:app-shell`.
- `module build`: команда `:app-shell:compileDebugUnitTestKotlin` успешно
  компилирует production code и узкий тестовый исходник.
- `public contract`: будущий потребитель модуля получает небольшой публичный
  API: `initial()`, `selectedDestination`, `selectedDestinations` и
  `select(destination)`.
- `consumer integration expectation`: будущий Compose root может читать одно
  выбранное направление и передавать destination обратно в `select(...)`.
- `dependency graph direction`: контракт состояния не импортирует app module,
  Android framework, Compose UI, storage, network или содержимое feature.
- `app-shell wiring responsibility`: связывание приложения, навигационные
  поверхности и Compose UI остаются вне `task-002`; эта задача отвечает только
  за состояние выбора.

## Граница изменений

Команда:

```text
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform android --feature app-shell --change app-shell --task task-002 --baseline Android/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-002.json --expected-sha256 coordinator-held-token
```

Результат: `Implementation scope: VALID (check)`.
