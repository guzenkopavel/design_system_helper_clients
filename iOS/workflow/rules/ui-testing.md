# iOS UI testing

UI flow начинается с observable scenario и чистого/описанного state. Selector
priority: accessibility identifier → stable text → index → coordinates с
обоснованием. Identifier не заменяет VoiceOver label.

Plan для UI включает launch/reset/fixture strategy, mapping steps→assertions,
проверку дерева accessibility и simulator evidence до/после действия. Build не
доказывает видимость identifier или корректный hit target.
