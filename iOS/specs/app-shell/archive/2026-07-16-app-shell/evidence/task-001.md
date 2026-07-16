# Evidence — task-001

## Summary

`task-001` выполнен в границе app-shell composition. Корневой путь больше не
передаёт `managedObjectContext` в `ContentView`, а технический Core Data list с
add/delete/detail interactions удалён из текущей root surface.

## Changed paths

- `iOS/SysDevScen/SysDevScen/SysDevScenApp.swift`
- `iOS/SysDevScen/SysDevScen/ContentView.swift`

`Persistence.swift` и `project.pbxproj` не изменялись: task не требовал cleanup
за пределами root path и не создавал новый target или package.

## Focused checks

Команда выполнена через watchdog:

```bash
bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 120 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
```

Результат: `PASS`, `** BUILD SUCCEEDED **`.

Watchdog limits: max 900s, stall 120s, output 20000 lines. Первичная попытка
запуска watchdog напрямую вернула `Permission denied`, поэтому тот же script был
запущен через `bash` без изменения лимитов и без обхода watchdog.

## Static scope review

- `application boundary`: приложение сохраняет только вход, жизненный цикл и
  обязанности корневой composition.
- Новая физическая единица не создана: нет нового `package`, Swift package
  target или non-application Xcode target.
- В корневом пути больше нет взаимодействия с Core Data: из `ContentView`
  удалены `@FetchRequest`, `managedObjectContext`, список, controls добавления и
  удаления, а также detail navigation.
- Data/network ownership не добавлялся.
- Android, harness и остальные несвязанные изменения worktree не менялись в
  рамках этой задачи.

## Residual scope

`task-002` остаётся pending и должен добавить утверждённую нативную UI shell
поверхность с тремя направлениями, выбранностью, accessibility и UX checks.
