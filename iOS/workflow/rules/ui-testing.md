# iOS UI testing

UI flow начинается с observable scenario и чистого/описанного state. Selector
priority: accessibility identifier → stable text → index → coordinates с
обоснованием. Identifier не заменяет VoiceOver label.

Plan для UI включает launch/reset/fixture strategy, mapping steps→assertions,
проверку дерева accessibility и simulator evidence до/после действия. Build не
доказывает видимость identifier или корректный hit target.

## Надёжность

- Ждать observable condition, а не фиксированный sleep.
- Test data контролируется локальным fixture/stub или документированным stable
  environment; live network делает результат UNKNOWN/flaky.
- Каждый test независим от порядка и очищает созданное состояние.
- Assertion проверяет пользовательский outcome, а не внутренний view hierarchy,
  если hierarchy не является accessibility contract.
- Failure сохраняет screenshot, hierarchy и relevant logs в bounded evidence.

Simulator/device, runtime, scheme и command обнаруживаются. Параллельный запуск
разрешён только при изолированных data/device resources. Один удачный retry не
стирает первый failure.

## Xcode runner recovery

Если широкий `xcodebuild test` для UI automation зависает или долго молчит до
первого `Test Suite`/`Running tests` output, это сначала классифицируется как
runner/runtime `UNKNOWN`, а не как product PASS или product FAIL. Evidence
фиксирует исходную команду, длительность, watchdog/stall budget, diagnostics и
причину остановки.

После такого runner-сбоя допустим один bounded recovery path: очистить только
ресурсы simulator/test runner, которыми владеет текущий запуск, отключить
параллельность через `-parallel-testing-enabled NO` и заменить широкий suite
на набор focused `-only-testing:` команд, если они покрывают ту же method
matrix. Focused PASS может закрыть terminal verification только когда исходный
runner-сбой сохранён как evidence, а отчёт явно объясняет покрытие широкого
suite более мелкими наблюдениями. Бесконечные rerun и удаление чужих booted
simulators запрещены.
