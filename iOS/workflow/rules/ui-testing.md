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
