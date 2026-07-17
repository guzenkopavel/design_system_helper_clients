# Runtime verify для `:app` после recovery

## Статус

`PASS`

## Команда

```text
ANDROID_SERIAL=emulator-5554 rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 180 --max-output-lines 4000 -- ./Android/gradlew -p Android :my-profile:connectedDebugAndroidTest :app:connectedDebugAndroidTest --console=plain
```

## Наблюдение

Подключённый эмулятор `Pixel_6(AVD) - 16` был загружен до
`sys.boot_completed=1`. Runtime-команда завершилась успешно; для `:app`
выполнено 22 instrumentation tests без пропусков и падений. Проверка покрыла
интеграцию профиля с оболочкой приложения на подключённом runtime.
