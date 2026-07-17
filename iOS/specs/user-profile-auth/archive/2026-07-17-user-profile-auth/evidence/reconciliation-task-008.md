# Reconciliation evidence — task-008

## Summary

Production baseline для корневой композиции подготовлен. Старые template-тесты
заменены app-shell state/UI тестами. `ContentView` очищен от Core Data.
`SysDevScenApp` обновлён для маршрутизации.

## Changed paths

- `iOS/SysDevScen/SysDevScen/ContentView.swift` — M, template cleanup
- `iOS/SysDevScen/SysDevScen/SysDevScenApp.swift` — M, root routing
- `iOS/SysDevScen/SysDevScenTests/SysDevScenTests.swift` — D, replaced
- `iOS/SysDevScen/SysDevScenUITests/SysDevScenUITests.swift` — D, replaced
- `iOS/SysDevScen/SysDevScenTests/AppShellStateTests.swift` — A, new
- `iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift` — A, new

## Discovered command

```
xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
```

## Watchdog

```
bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 120 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
```

## Verification

Build succeeded. Production paths cover task-008 scope: root composition,
test migration, template removal.
