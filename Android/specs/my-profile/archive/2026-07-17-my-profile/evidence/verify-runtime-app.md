# Runtime verify для `:app`

## Статус

`UNKNOWN`

## Команда

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 2500 -- ./Android/gradlew -p Android :app:connectedDebugAndroidTest --console=plain
```

## Наблюдение

Instrumentation APK и runtime test graph для приложения-потребителя были собраны
до границы запуска, но команда завершилась с
`com.android.builder.testing.api.DeviceException: No connected devices!`.
Наблюдаемая интеграция профиля внутри root app, auth gate recovery, нижней
навигации и native UI runtime остаётся `UNKNOWN`.
