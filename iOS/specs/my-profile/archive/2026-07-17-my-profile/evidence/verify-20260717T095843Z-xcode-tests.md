# Свежая проверка Xcode tests

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 90 --max-output-lines 60000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' test`
- Destination: `iPhone 17`, iOS Simulator `26.5`
- Exit status: `0`
- Result: `PASS` для выполненного набора
- Duration: `454.25s`
- Xcresult: `/Users/pavel/Library/Developer/Xcode/DerivedData/SysDevScen-bdowkpzdxhavojgpkycvjqozgfjp/Logs/Test/Test-SysDevScen-2026.07.17_16-59-08-+0700.xcresult`

Итог Xcode — `TEST SUCCEEDED`. Прошли 5 `AppShellStateTests`, 5
`MyProfileUITests`, 6 `AuthFlowUITests`, 3 `AppShellUITests` и launch tests.
Профильный набор наблюдал содержимое и счётчик без навигации, пустое
недоступное состояние, ошибку истории, восстановление недействительной сессии и
успешный выход к пустому email.

Во время параллельного запуска один clone получил
`FBSOpenApplicationServiceErrorDomain` для UI runner, однако Xcode завершил
полный запланированный набор как `TEST SUCCEEDED`, а перечисленные профильные
тесты имеют отдельные passed results. Набор не переключал VoiceOver, Dynamic
Type, light/dark/increased contrast, Reduce Motion/Transparency либо iPad.
