# task-001 — корневая composition и application boundary

- Layer: infrastructure
- Boundary owner: app-shell composition boundary inside `SysDevScen` application target
- Engineering scopes: ["application"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Estimate (ideal): 0.5-1.0 days
- Paths: existing: iOS/SysDevScen/SysDevScen/SysDevScenApp.swift; existing: iOS/SysDevScen/SysDevScen/ContentView.swift; existing: iOS/SysDevScen/SysDevScen/Persistence.swift; existing: iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj

## Goal

Подготовить root composition для app shell: убрать из корневого пути передачу
Core Data context, сохранить application target только как entry/lifecycle/root
routing/dependency wiring/config/resources и не создавать отдельный package или
target.

## Inline contract context

Покрывает `REQ-1`, `REQ-2`, `REQ-4`, `AC-1`, `AC-2`, `AC-4`, `IOS-REQ-1`,
`IOS-REQ-3`, `IOS-AC-1` и `IOS-AC-3`. Задача отвечает за путь запуска,
начальную композицию, отсутствие технического шаблона и application boundary.

## Steps

- В `SysDevScenApp.swift` заменить root composition так, чтобы app shell больше
  не получал `managedObjectContext` через корневой view.
- В `ContentView.swift` оставить только seam корневой shell-композиции и удалить
  Core Data list, add/delete, detail navigation и persistence interactions из
  нового корневого пути.
- Не удалять `Persistence.swift` и model за пределами owned root path, если это
  не требуется текущим package; они остаются template evidence вне новой
  composition.
- Проверить `application boundary`: application target сохраняет только
  разрешённые обязанности входа, жизненного цикла, корневой маршрутизации,
  связывания зависимостей, платформенной настройки и target-resources.

## Verification

- Discovered command: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build`
- Watchdog max/stall/output budget for nontrivial checks: build max 900s, stall 120s, output 20MB.
- Applicable rule/check mapping: `application boundary`, app-shell allowlist,
  отсутствие нового package, отсутствие нового target, отсутствие Core Data root
  interaction и отсутствие data/network ownership.

## Expected result

Build проходит, корневой путь больше не зависит от Core Data context injection,
а static review подтверждает `application boundary` и записанное решение
`not-applicable` по modularity.

## Out of scope

Нативные labels, visual treatment, simulator accessibility сценарии,
переиспользуемая UI capability, данные, сеть, cleanup хранения вне корневого
пути и Android.
