# Локальные команды verify после recovery

## Статус

`PASS`

## Команда

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 2600 -- ./Android/gradlew -p Android :my-profile:testDebugUnitTest :my-profile:lintDebug :my-profile:assembleDebug :app-shell:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug --console=plain
```

## Наблюдение

Свежая локальная команда после recovery завершилась успешно. Проверены
модульные тесты, lint и сборка `:my-profile`, модульные тесты `:app-shell`,
модульные тесты `:app` и debug-сборка приложения-потребителя.
