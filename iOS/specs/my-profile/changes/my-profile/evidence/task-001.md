# Доказательства задачи — task-001

## Итог

Открыта минимальная публичная граница сессии в `AuthFeature`: профильная функция получает `AuthSessionRequesting`, ограниченный `AuthSessionRequest` для `profile`, `interviewHistory` и `logout`, а также `AuthSessionResponse` без доступа к Keychain secret или cookie storage. `AuthFeatureFactory` собирает привязанный к сессии клиент, `DefaultAuthAPIClient` выполняет HTTPS request с текущим `dsh_session`, `401` мапится в `AuthError.sessionInvalid`, успешный logout очищает secret, а восстанавливаемая ошибка backend при logout secret не удаляет.

## Технические доказательства

iOS/AuthFeature/Sources/AuthFeature/Domain/AuthSessionRequesting.swift | добавлен | публичный ограниченный `session request/response/protocol` для consumer package
iOS/AuthFeature/Sources/AuthFeature/Data/DefaultAuthSessionRequestClient.swift | добавлен | internal `Keychain-backed session requester` без раскрытия secret
iOS/AuthFeature/Sources/AuthFeature/Data/DefaultAuthAPIClient.swift | изменен | `session-bound request route`, корректный `Cookie header`, безопасная нормализация headers
iOS/AuthFeature/Sources/AuthFeature/AuthFeatureFactory.swift | изменен | публичная factory entrypoint для `any AuthSessionRequesting`
iOS/AuthFeature/Sources/AuthFeature/Domain/AuthError.swift | изменен | typed `AuthError.sessionInvalid` доступен consumer package
iOS/AuthFeature/Tests/AuthFeatureTests/Data/DefaultAuthAPIClientTests.swift | изменен | тесты на `cookie forwarding`, `profile route`, `logout route`, `401 mapping` и `logout failure recovery`
iOS/AuthFeature/Tests/AuthFeatureTests/AuthFeatureFactoryTests.swift | изменен | approved public API surface включает новую минимальную границу

## Проверки

- Узкая RED-проверка: `bash workflow/scripts/test-watchdog.sh --max-seconds 120 --stall-seconds 30 --max-output-lines 20000 -- swift test --package-path iOS/AuthFeature --filter DefaultAuthAPIClientTests` — PASS, первый запуск упал до production implementation, потому что новая граница сессии и injectable session еще отсутствовали.
- Узкая GREEN-проверка: `bash workflow/scripts/test-watchdog.sh --max-seconds 120 --stall-seconds 30 --max-output-lines 20000 -- swift test --package-path iOS/AuthFeature --filter DefaultAuthAPIClientTests` — PASS, 12 tests.
- Регрессионная проверка package: `bash workflow/scripts/test-watchdog.sh --max-seconds 120 --stall-seconds 30 --max-output-lines 20000 -- swift test --package-path iOS/AuthFeature` — PASS, 50 tests.
- Проверка scope: `workflow/scripts/validate-implementation-scope.py check --platform ios --feature my-profile --change my-profile --task task-001 --baseline iOS/specs/my-profile/changes/my-profile/evidence/scope-baseline-task-001.json --expected-sha256 coordinator-held-sha256` — PASS.

## Остаточные риски

Проводка Xcode project и сборка consumer `MyProfileFeature` остаются в следующих task scope; текущая задача проверила публичный package-level contract и отсутствие зависимости `AuthFeature` от будущего profile package.
