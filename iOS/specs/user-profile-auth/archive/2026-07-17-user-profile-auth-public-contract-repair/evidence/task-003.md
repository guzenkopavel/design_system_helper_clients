# Доказательства задачи — task-003

## Итог

Добавлен app-level набор `AuthFlowUITests` для авторизации на детерминированной
заглушке. Тесты покрывают запуск без сессии, отсутствие вкладок оболочки до
активной сессии, ветвление существующей почты во «Вход», ветвление новой почты
в «Регистрацию», возврат к редактируемой почте, успешный вход и успешную
регистрацию с переходом в оболочку «Кейсы». Обычный запуск приложения остаётся
на живом сервере `https://89.125.1.21.nip.io`; сквозные тесты намеренно
используют `--auth-stub-signed-out`, чтобы не зависеть от внешнего состояния
сервера.

## Технические доказательства

`iOS/SysDevScen/SysDevScenUITests/AuthFlowUITests.swift` | add | добавлены сценарии запуска без сессии, ветвления входа, ветвления регистрации, возврата к почте, успешного входа и успешной регистрации.

```text
rtk bash ../../workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 120 --max-output-lines 9000 -- xcodebuild test -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:SysDevScenUITests/AuthFlowUITests
rtk bash ../../workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 150 --max-output-lines 10000 -- xcodebuild test -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:SysDevScenUITests
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform ios --feature user-profile-auth --change user-profile-auth-public-contract-repair --task task-003 --baseline iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/evidence/scope-baseline-task-003.json
```

## Проверки

- Сфокусированные проверки: `SysDevScenUITests/AuthFlowUITests` — `PASS`, 6 тестов, 0 отказов.
- Дополнительное покрытие: весь `SysDevScenUITests` — `PASS`, auth, shell и launch screenshot сценарии прошли.
- Проверка scope: `validate-implementation-scope.py check` — `PASS`.

## Остаточные риски

Команда `xcodebuild` завершилась успешно, но после `TEST SUCCEEDED` в выводе
остался шум `CoreSimulator` про отдельные clone runner launches. Этот шум не
сломал проверяемые сценарии и не изменил результат команды. Живой backend path
требует отдельной terminal verification, потому что эта задача проверяет
детерминированные сценарии пользовательского флоу.
