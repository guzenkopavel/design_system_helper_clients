# task-002 — нативная SwiftUI shell-поверхность

- Layer: presentation
- Boundary owner: local SwiftUI app-shell root surface
- Engineering scopes: ["ui"]
- Depends on: task-001
- Status: pending
- Evidence: none
- Estimate (ideal): 1.0-1.5 days
- Paths: existing: iOS/SysDevScen/SysDevScen/ContentView.swift; existing: iOS/SysDevScen/SysDevScen/Assets.xcassets; existing: iOS/specs/app-shell/changes/app-shell/platform-ux.md

## Goal

Реализовать нативную SwiftUI-поверхность app shell с тремя направлениями
«Кейсы», «Знания», «Профиль», начальным выбором «Кейсы», ровно одним selected
state и нейтральными поверхностями без фиктивного контента.

## Inline contract context

Покрывает `REQ-1`, `REQ-2`, `REQ-3`, `REQ-5`, `REQ-6`, `AC-1`, `AC-2`, `AC-3`,
`AC-5`, `IOS-REQ-2` и `IOS-AC-2`. Задача отвечает за нативные controls,
семантику выбора, видимые русские labels и UX adapter constraints.

## Steps

- Ввести закрытый value type `RootSection` для трёх разделов и локальное
  действие выбора без history и без второго state owner.
- Использовать `standard components` и `navigation` для `functional controls`;
  если будет выбран `Liquid Glass`, проверить доступность SDK и применять его
  только к управляющим элементам и навигации, не к `content background`.
- Сохранить exact order «Кейсы», «Знания», «Профиль», initial selection «Кейсы»
  и ровно один selected state.
- Применить `platform-ux.md`: проверить `Liquid Glass`, `light/dark`,
  `increased contrast`, `Reduce Transparency`, `Reduce Motion` и
  `older-OS/SDK fallback`.
- Выполнить scope checks `simulator`, `accessibility` и `design-system`: labels,
  roles, selected state, non-color cue, `Dynamic Type`, hit areas и отсутствие
  локальных литералов цвета, шрифта и отступов.

## Verification

- Discovered command: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build`
- Watchdog max/stall/output budget for nontrivial checks: build max 900s, stall 120s, output 20MB; visual simulator inspection max 1200s, stall 180s, output 30MB.
- Applicable rule/check mapping: `platform-ux.md`, `Liquid Glass`, `light/dark`,
  `increased contrast`, `Reduce Transparency`, `Reduce Motion`,
  `older-OS/SDK fallback`, `simulator`, `accessibility`, `design-system`.

## Expected result

На simulator доступна shell-поверхность с тремя directions, выбранными
«Кейсами», корректным переключением и нативной accessibility семантикой.
Selected state различим не только цветом, visual treatment следует
`platform-ux.md`, а content background не становится glass.

## Out of scope

Реальный контент разделов, загрузка network/data, analytics, localization
scope, новый reusable UI component и изменения Android остаются вне задачи.
