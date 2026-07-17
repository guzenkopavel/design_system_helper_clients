# Свежая проверка MyProfileFeature

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 180 --stall-seconds 45 --max-output-lines 25000 -- swift test --package-path iOS/MyProfileFeature`
- Environment: `arm64e-apple-macos14.0`
- Exit status: `0`
- Result: `PASS` для выполненных тестов
- Duration: `0.90s`

Выполнены 16 тестов без сбоев. Проверены полная пагинация, преобразование
offline/401/backend ошибок, сбой выхода, единственная активная загрузка, отмена
устаревшего обновления, состояния presentation, сообщение счётчика и ветви
Reduce Motion/Reduce Transparency.

SwiftPM снова сообщил, что
`Sources/MyProfileFeature/Resources/Localizable.ru.strings` является unhandled
file: manifest не объявляет ресурс. Чтение исходного файла тестом не доказывает
локализацию packaged runtime.
