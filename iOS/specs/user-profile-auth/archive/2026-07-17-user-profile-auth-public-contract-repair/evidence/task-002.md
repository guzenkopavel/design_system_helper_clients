# Доказательства задачи — task-002

## Итог

`AuthFeature` подключён к `SysDevScen` как локальный пакет и стал
потребляемым приложением через публичный контракт. Корневая композиция
`SysDevScenApp` создаёт `AuthSessionModel`, обычный запуск использует живой
сервер `https://89.125.1.21.nip.io`, а детерминированные сценарии заглушки
доступны только через явные аргументы запуска. Новый `RootView` показывает
загрузку, `AuthFlowView` или существующую оболочку по `SessionState`.
Существующие тесты оболочки запускают активную заглушку и продолжают
проверять оболочку без прохождения авторизации.

## Технические доказательства

`iOS/AuthFeature/Package.swift` | change | опубликован library product `AuthFeature` для потребителя пакета.
`iOS/AuthFeature/Sources/AuthFeature/AuthFeatureFactory.swift` | change | добавлен вложенный `StubScenario` и публичная фабрика заглушки без новых публичных top-level типов.
`iOS/SysDevScen/SysDevScen/RootView.swift` | add | добавлена корневая маршрутизация `.checking`, `.signedOut`, `.active`.
`iOS/SysDevScen/SysDevScen/SysDevScenApp.swift` | change | добавлена композиция `AuthSessionModel`, живой URL по умолчанию и аргументы запуска заглушки.
`iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj` | change | локальный package `../AuthFeature` подключён к цели приложения.
`iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift` | change | набор тестов оболочки запускает активную сессию заглушки.
`iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/plan/task-002.md` | change | task Paths уточнены для `Package.swift`, потому что потребитель `Xcode` требует опубликованный product.

```text
rtk bash ../../workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 90 --max-output-lines 6000 -- xcodebuild test -scheme AuthFeature-Package -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5'
rtk bash ../../workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 120 --max-output-lines 8000 -- xcodebuild -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
rtk bash ../../workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 120 --max-output-lines 8000 -- xcodebuild test -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:SysDevScenUITests/AppShellUITests
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform ios --feature user-profile-auth --change user-profile-auth-public-contract-repair --task task-002 --baseline iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/evidence/scope-baseline-task-002.json
```

## Проверки

- Сфокусированные проверки: `AuthFeature-Package` — `PASS`, 45 тестов, 0 отказов.
- Сфокусированные проверки: `SysDevScen` build — `PASS`, `AuthFeature` присутствует в графе зависимостей цели.
- Сфокусированные проверки: `SysDevScenUITests/AppShellUITests` — `PASS`, 3 теста, 0 отказов.
- Проверка scope: `validate-implementation-scope.py check` — `PASS`.

## Остаточные риски

Сквозные сценарии входа и регистрации остаются в scope следующей задачи
`task-003`. Проверка живого сервера `https://89.125.1.21.nip.io` в этой задаче
не выполнялась: `task-002` доказывает интеграцию приложения и живой путь
конфигурации по умолчанию, а не terminal backend verification.
