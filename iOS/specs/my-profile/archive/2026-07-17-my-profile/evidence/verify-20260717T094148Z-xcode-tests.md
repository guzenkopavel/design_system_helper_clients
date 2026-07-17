# Fresh verification: Xcode tests and bounded recovery

## Initial full run

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 90 --max-output-lines 60000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' test`
- Exit status: `126`
- Result: `UNKNOWN`
- Observation: simulator clone failed to launch `none.SysDevScen` with `NSMachErrorDomain Code=-308`; after 90 seconds without output watchdog stopped the run. Итог Xcode: `BUILD INTERRUPTED`.

## Focused app-shell recovery

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 90 --max-output-lines 60000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenTests test`
- Exit status: `0`
- Result: `PASS`
- Duration: `69.44s`
- Observation: выполнены 5 `AppShellStateTests` без сбоев; Xcode сохранил xcresult в `Test-SysDevScen-2026.07.17_16-36-31-+0700.xcresult`.

## Focused profile UI recovery

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 90 --max-output-lines 60000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests test`
- Exit status: `0`
- Result: `PASS`
- Duration: `153.46s`
- Observation: выполнены 5 `MyProfileUITests` без сбоев. Наблюдены content/count/no-navigation, empty-disabled, history-error, invalid-session recovery и successful logout к пустому email. Xcode сохранил xcresult в `Test-SysDevScen-2026.07.17_16-38-14-+0700.xcresult`.
- Coverage limit: suite не наблюдает logout network failure, loading appearance, profile symbol geometry, VoiceOver order/announcements, Dynamic Type, light/dark/increased contrast, Reduce Motion/Transparency appearance либо iPad.
