# Fresh verification: MyProfileFeature

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 180 --stall-seconds 45 --max-output-lines 25000 -- swift test --package-path iOS/MyProfileFeature`
- Environment: `arm64e-apple-macos14.0`
- Exit status: `0`
- Result: `PASS` для выполненных тестов
- Duration: `30.00s`
- Observation: выполнены 16 тестов без сбоев. Проверены полная пагинация, mapping offline/401/backend, logout failure, single active reload, отмена stale update, presentation states, count feedback и ветви Reduce Motion/Reduce Transparency.
- Diagnostic: SwiftPM сообщил, что `Sources/MyProfileFeature/Resources/Localizable.ru.strings` является unhandled file; manifest не объявляет этот ресурс. Поэтому тест чтения исходного файла не доказывает packaged localization runtime behavior.
