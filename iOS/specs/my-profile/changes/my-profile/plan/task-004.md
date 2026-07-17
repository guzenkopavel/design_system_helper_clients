# task-004 — App-shell wiring and UI evidence

- Layer: infrastructure
- Boundary owner: SysDevScen app-shell composition boundary
- Engineering scopes: ["application", "package", "ui"]
- Depends on: task-003
- Status: pending
- Evidence: none
- Estimate (ideal): 1-2 days
- Read-only context: ["iOS/AuthFeature/Package.swift", "iOS/SysDevScen/SysDevScen.xcodeproj/project.xcworkspace/contents.xcworkspacedata", "iOS/specs/my-profile/changes/my-profile/implementation-spec.md", "iOS/specs/my-profile/changes/my-profile/platform-ux.md", "specs/product/my-profile/spec.md"]
- Paths: existing: iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj; existing: iOS/SysDevScen/SysDevScen/ContentView.swift; existing: iOS/SysDevScen/SysDevScen/RootView.swift; existing: iOS/SysDevScen/SysDevScen/SysDevScenApp.swift; existing: iOS/SysDevScen/SysDevScenTests; existing: iOS/SysDevScen/SysDevScenUITests

## Goal

Подключить `MyProfileFeature` как `package consumer` в `SysDevScen`, заменить `profile tab placeholder` на `package factory` и добавить `focused app-shell/UI tests` без переноса владения feature в `application shell`.

## Inline contract context

`REQ-1`, `REQ-4`, `REQ-6`, `REQ-8`, `REQ-9`, `REQ-10`, `AC-1`, `AC-4`, `AC-5`, `AC-7`, `AC-8`, `AC-12`, `AC-13`, `AC-14`, `AC-15`, `AC-16`, `AC-17` и `AC-18` требуют `observable profile tab`, `count message`, `logout recovery`, parity и проверки `accessibility appearance`. `IOS-REQ-1`, `IOS-REQ-4`, `IOS-REQ-5`, `IOS-AC-1`, `IOS-AC-2`, `IOS-AC-5`, `IOS-AC-6` и `IOS-AC-7` требуют `app-shell composition only`, `package dependency`, `signed-out recovery`, runtime-сценарии profile UI и `native UX evidence`.

## Implementation deliverables

- Project `SysDevScen` подключает product `MyProfileFeature` и сохраняет `app-shell composition allowlist`.
- Пользовательские UI tests подтверждают вкладку профиля, сообщение счётчика и восстановление выхода.

## Steps

Обновить `project.pbxproj` по обнаруженному `local package pattern` для `../AuthFeature`, добавив `local package product` `MyProfileFeature` только в нужный `app target`. В `SysDevScenApp` создать зависимости рядом с `auth configuration`; в `RootView`/`ContentView` передать `package factory` и `logout callback`, который вызывает `AuthSessionModel.invalidateSession`. `Application shell` остаётся ограничен `dependency-wiring`, `root-routing` и `target-resources`; `profile data`, `pagination`, `mutable feature state` и сетевой слой остаются в package. Добавить `app-shell tests` на `boundary allowlist` и `dependency graph`, плюс `UI tests` с `launch arguments/stubs` для `content`, `empty history`, `history error`, `invalid session` и `logout`. Доказательства UI должны покрыть `simulator`, `accessibility`, `design-system`, `platform-ux.md`, `Liquid Glass`, `light/dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion`, `older-OS/SDK fallback`, `hit targets` и отсутствие навигации после `count message`.

## Verification

- Discovered command: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' build`
- Discovered command: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' test`
- Watchdog max/stall/output budget for nontrivial checks: build max 300s, stall 60s, output 40000 lines; test max 600s, stall 90s, output 60000 lines
- Applicable rule/check mapping: `package consumer`, `consumer integration`, `package build`, `public contract`, `dependency graph`, `app-shell wiring`, `application boundary`, `simulator`, `accessibility`, `design-system`, `platform-ux.md`, `Liquid Glass`, `light/dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion`, `older-OS/SDK fallback`

## Expected result

Consumer build и UI tests проходят, вкладка профиля рендерится через `MyProfileFeature`, `logout` возвращает к пустому вводу email, app-shell diff содержит только composition and dependency wiring, а `native obligation evidence` готово для Verify.

## Out of scope

Изменения `backend`, `Android implementation`, `interview list navigation`, `analytics` и `product contract edits` исключены из этой задачи.
