# Runtime verify для `:my-profile`

## Статус

`UNKNOWN`

## Команда

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 2500 -- ./Android/gradlew -p Android :my-profile:connectedDebugAndroidTest --console=plain
```

## Наблюдение

Instrumentation APK и runtime test graph для `:my-profile` были собраны до
границы запуска, но команда завершилась с
`com.android.builder.testing.api.DeviceException: No connected devices!`.
Репрезентативный emulator/device недоступен, поэтому appearance, TalkBack,
font scaling, light/dark, contrast, motion и device adaptation не получают
terminal `PASS`.
