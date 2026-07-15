# task-001 — Import generated iOS scaffold

- Layer: presentation
- Engineering scopes: ["application", "ui", "xcode"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Estimate (ideal): 0.5–1 days
- Paths: existing: iOS/SysDevScen/

## Goal

Capture the generated iOS project as a reproducible, buildable baseline for subsequent feature implementation.

## Inline contract context

IOS-REQ-1 requires the buildable shell, while IOS-AC-1 requires focused Xcode build evidence for the discovered scheme.

## Steps

Retain the application boundary, generated SwiftUI shell, Core Data resources, assets, Xcode targets, and template tests.

## Verification

- Discovered command: xcodebuild build -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17,OS=26.5'
- Watchdog max/stall/output budget for nontrivial checks: 180 seconds / 60 seconds / 2500 lines
- Applicable rule/check mapping: verify the application boundary, simulator build configuration, accessibility surface, and design-system scope without claiming successful test execution.

## Expected result

The application scheme builds for the discovered simulator and machine-local Xcode state remains outside version control.

## Out of scope

Product scenarios, final navigation, simulator test recovery, and terminal verification remain outside this task.
