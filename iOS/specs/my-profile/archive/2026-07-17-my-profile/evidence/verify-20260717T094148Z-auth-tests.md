# Fresh verification: AuthFeature

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 120 --stall-seconds 30 --max-output-lines 20000 -- swift test --package-path iOS/AuthFeature`
- Environment: `arm64e-apple-macos14.0`
- Exit status: `0`
- Result: `PASS`
- Duration: `5.07s`
- Observation: выполнены 50 тестов без сбоев. Фокусные `AuthSessionRequestClientTests` подтвердили передачу cookie, маршруты profile/logout, очистку секрета после успешного logout, сохранение секрета при backend failure и mapping 401 в `invalidSession`.
