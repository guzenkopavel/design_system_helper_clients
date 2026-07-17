# Fresh verify: MyProfileFeature

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 180 --stall-seconds 45 --max-output-lines 25000 -- swift test --package-path iOS/MyProfileFeature`
- Environment: macOS host, Swift 6.3 package toolchain
- Exit status: `0`
- Duration: `1.51s`
- Result: `PASS`
- Observation: выполнено `16` тестов, failures `0`, unexpected `0`.

Тесты подтвердили полную пагинацию, profile/history/logout requests, mapping
ошибок, invalid-session recovery, logout failure, single-active-load,
cancellation/stale-update protection, состояния presentation и русские строки.

SwiftPM также сообщил warning: файл
`iOS/MyProfileFeature/Sources/MyProfileFeature/Resources/Localizable.ru.strings`
не объявлен как resource и не исключён в manifest. Это не изменило exit status,
но означает, что runtime resource packaging данным запуском не доказан.
