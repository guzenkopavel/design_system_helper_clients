# Итог

Интеграционные и доступностные проверки доведены до рабочего состояния.
Свежий полный запуск `app:connectedDebugAndroidTest` на обнаруженном AVD прошёл:
19 тестов выполнены, 0 ошибок. Быстрый слой `:auth:testDebugUnitTest`,
`:app:testDebugUnitTest` и `:app:compileDebugAndroidTestKotlin` также зелёный.
Добавлен сквозной сценарий регистрации: новая почта переводит экран на
«Регистрация», ввод пароля вызывает `register()`, не вызывает `login()`,
сохраняет сессию и открывает раздел «Кейсы».

По результатам первого запуска на устройстве устранены подтверждённые блокеры:
`AuthGate` больше не падает при отсутствии `auth_api_base_url`, внедрённый
`AuthViewModel` пересоздаётся для новых тестовых зависимостей, пароль реально
обновляется локально в `AuthScreen`, поле пароля получает фокус при переходе
на второй шаг, тема приложения по умолчанию отключает динамические цвета и
использует мягко-синий запасной вариант. Старый `AppShellIntegrationTest` переведён на прямую
проверку оболочки, потому что запуск `MainActivity` теперь по контракту
начинается со шлюза авторизации.

# Технические доказательства

M Android/auth/src/main/java/ru/home/sysdevsc/auth/AuthGate.kt
M Android/auth/src/main/java/ru/home/sysdevsc/auth/ui/AuthScreen.kt
M Android/app/src/main/java/ru/home/sysdevsc/ui/theme/Color.kt
M Android/app/src/main/java/ru/home/sysdevsc/ui/theme/Theme.kt
M Android/app/src/androidTest/java/ru/home/sysdevsc/AppShellIntegrationTest.kt
A Android/app/src/androidTest/java/ru/home/sysdevsc/AuthIntegrationTest.kt
A Android/app/src/androidTest/java/ru/home/sysdevsc/AuthAccessibilityTest.kt
M Android/specs/user-profile-auth/changes/user-profile-auth/evidence/task-005.md

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 2500 -- ./Android/gradlew -p Android --no-daemon :app:compileDebugAndroidTestKotlin --console=plain
Первая фокусированная компиляция: успешно за 18 секунд; код выхода 0.
```

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 2500 -- ./Android/gradlew -p Android --no-daemon :auth:testDebugUnitTest :app:testDebugUnitTest --console=plain
Сборка и модульные тесты: успешно за 22 секунды; код выхода 0.
```

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 3000 -- ./Android/gradlew -p Android --no-daemon :auth:testDebugUnitTest :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin --console=plain
Быстрый слой после исправлений: успешно за 33 секунды; код выхода 0.
```

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 180 --max-output-lines 5000 -- ./Android/gradlew -p Android --no-daemon app:connectedDebugAndroidTest --console=plain
На Pixel_6(AVD) - 16 выполнено 18 тестов.
Итог: успешно за 2 минуты 27 секунд; код выхода 0.
```

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 3000 -- ./Android/gradlew -p Android --no-daemon :auth:testDebugUnitTest :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin --console=plain
Быстрый слой после добавления регистрации: успешно за 26 секунд; код выхода 0.
```

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 180 --max-output-lines 5000 -- ./Android/gradlew -p Android --no-daemon app:connectedDebugAndroidTest --console=plain
На Pixel_6(AVD) - 16 выполнено 19 тестов.
Итог: успешно за 3 минуты 21 секунду; код выхода 0.
```

```text
rtk python3 workflow/scripts/validate-implementation-scope.py snapshot --platform android --feature user-profile-auth --change user-profile-auth --task task-005 --baseline Android/specs/user-profile-auth/changes/user-profile-auth/evidence/scope-baseline-task-005.json
Снимок области: валиден.
```

Эмуляторный запуск подтвердил границу приложения, наличие эмулятора,
доступность, дизайн-систему, светлое и тёмное оформление Material 3, доступные
цветовые роли, отключённые динамические цвета и мягко-синий запасной вариант.
Отдельный системный режим повышенного контраста не управлялся доступной средой;
покрытие ограничено проверяемыми утверждениями контраста ролей Material.
