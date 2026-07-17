# Локальные команды verify

## Статус

`PASS`

## Команда

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 2400 -- ./Android/gradlew -p Android :my-profile:testDebugUnitTest :my-profile:lintDebug :my-profile:assembleDebug :app-shell:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug --console=plain
```

## Наблюдение

Команда завершилась успешно. Свежая проверка покрыла unit tests модуля профиля,
lint и сборку `:my-profile`, unit tests `:app-shell`, unit tests `:app` и
debug-сборку приложения-потребителя. Gradle обнаружил `:my-profile`,
`:app-shell`, `:auth` и `:app`; сборочный граф подтвердил наличие отдельной
Android library capability и consumer dependency.
