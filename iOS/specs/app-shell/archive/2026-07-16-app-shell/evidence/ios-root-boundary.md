# Evidence IOS-REQ-1 — root boundary и dependency graph

Статус: PASS.

`SysDevScenApp.swift` содержит `WindowGroup { ContentView() }` и не передаёт
`managedObjectContext` в новый root path. Xcode project содержит один production
target `SysDevScen` и test targets `SysDevScenTests`, `SysDevScenUITests`;
новый package, production target или dependency product не добавлены.

`PBXFileSystemSynchronizedRootGroup` подключает существующие source folders, а
application target остаётся границей entry/lifecycle/root routing/config/resources.
Публичный API для app shell не вводился: `RootShellView` и `RootSection`
остаются private.
