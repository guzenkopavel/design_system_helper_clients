# task-003 — Native profile presentation

- Layer: presentation
- Boundary owner: MyProfileFeature SwiftUI presentation boundary
- Engineering scopes: ["localization", "ui"]
- Depends on: task-002
- Status: done
- Evidence: evidence/task-003.md
- Estimate (ideal): 1-1.5 days
- Read-only context: ["iOS/specs/my-profile/changes/my-profile/implementation-spec.md", "iOS/specs/my-profile/changes/my-profile/platform-ux.md", "specs/product/my-profile/spec.md", "specs/product/my-profile/ux.md"]
- Paths: proposed: iOS/MyProfileFeature/Sources/MyProfileFeature/Presentation; proposed: iOS/MyProfileFeature/Sources/MyProfileFeature/Resources; proposed: iOS/MyProfileFeature/Tests/MyProfileFeatureTests/Presentation

## Goal

Добавить `SwiftUI profile surface` внутри `MyProfileFeature` с русскими строками, `accessibility semantics`, устойчивостью `Dynamic Type` и `native visual behavior` из `platform-ux.md`.

## Inline contract context

`REQ-1`, `REQ-3`, `REQ-4`, `REQ-5`, `REQ-9`, `REQ-10`, `AC-1`, `AC-3`, `AC-4`, `AC-5`, `AC-6`, `AC-13`, `AC-14`, `AC-15`, `AC-16`, `AC-17` и `AC-18` требуют `profile symbol`, email, `action group`, `count feedback`, `disabled state`, `assistive semantics` и поддержку внешнего вида. `IOS-REQ-3`, `IOS-REQ-5`, `IOS-AC-5` и `IOS-AC-7` требуют `value-state rendering`, отсутствия навигации для `count message`, `Liquid Glass fallback`, `semantic roles` и `accessibility checks`.

## Implementation deliverables

- Поверхность SwiftUI показывает email, `profile symbol`, `action group` и `count feedback`.
- Localized resources покрывают русские labels без грамматически опасной конкатенации.

## Steps

Добавить `presentation views` и `view-state mapping` только внутри package. Использовать `standard components`, `standard profile symbol`, `semantic roles`, `content background and soft blue roles` без локальных цветовых литералов. `Liquid Glass` применять только для `functional controls/navigation-adjacent treatment` при availability; для `Reduce Transparency` и `older-OS/SDK fallback` использовать `system materials/standard components`. Добавить `localization resources` для «Мои интервью», «Выход», «Интервью: N» и `recovery messages` без грамматически опасной конкатенации. Добавить `presentation tests` или `view-inspection-friendly state tests` на `enabled/disabled actions`, `count feedback event`, `logout loading`, `accessibility labels/traits`, `light/dark`, `increased contrast`, `Reduce Motion` and `Reduce Transparency branches`.

## Verification

- Discovered command: `swift test --package-path iOS/MyProfileFeature`
- Watchdog max/stall/output budget for nontrivial checks: max 180s, stall 45s, output 25000 lines
- Applicable rule/check mapping: `simulator`, `accessibility`, `design-system`, `localization`, `platform-ux.md`, `Liquid Glass`, `light/dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion`, `older-OS/SDK fallback`

## Expected result

Package tests проходят, а presentation открывает `native SwiftUI surface` для `app-shell composition`, с `accessibility semantics`, `localized strings`, `Dynamic Type behavior` и `fallback decisions` из `platform-ux.md` для `simulator verification`.

## Out of scope

Project `project.pbxproj`, замена app tab и изменения UI test target остаются вне этой задачи presentation.
