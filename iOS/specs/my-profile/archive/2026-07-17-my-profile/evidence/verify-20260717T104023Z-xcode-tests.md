# Fresh verify: Xcode tests

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 90 --max-output-lines 60000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO test`
- Destination: iPhone 17, iOS 26.5 simulator
- Exit status: `0`
- Duration: `290.68s` testing elapsed
- Result: `PASS`
- xcresult: `/Users/pavel/Library/Developer/Xcode/DerivedData/SysDevScen-bdowkpzdxhavojgpkycvjqozgfjp/Logs/Test/Test-SysDevScen-2026.07.17_17-41-13-+0700.xcresult`

`SysDevScenUITests` выполнил `18` тестов без failures. Все пять
`MyProfileUITests` имеют `Passed`: content/count feedback без navigation,
empty-history disabled action, recoverable history error, invalid-session
recovery и logout к пустому email entry. `AppShellStateTests` выполнил пять
тестов без failures.

Запуск не включал отдельные профильные сценарии VoiceOver, Dynamic Type,
increased contrast, Reduce Motion, Reduce Transparency, iPad или older-OS.
Launch tests с dark appearance не открывали профиль и поэтому не доказывают
dark appearance профильной поверхности.
