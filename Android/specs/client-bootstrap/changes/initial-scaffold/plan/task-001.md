# task-001 — Import generated Android scaffold

- Layer: presentation
- Engineering scopes: ["application", "compose", "gradle", "ui"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Estimate (ideal): 0.5–1 days
- Paths: existing: Android/

## Goal

Capture the generated Android project as a reproducible, buildable baseline for subsequent feature implementation.

## Inline contract context

AND-REQ-1 requires the buildable shell, while AND-AC-1 requires focused wrapper-driven unit-test evidence.

## Steps

Retain the application boundary, Compose state baseline, Gradle task configuration, resources, and generated template tests.

## Verification

- Discovered command: Android/gradlew -p Android testDebugUnitTest
- Watchdog max/stall/output budget for nontrivial checks: 300 seconds / 90 seconds / 4000 lines
- Applicable rule/check mapping: verify the application boundary, Compose state, Gradle task, emulator readiness, accessibility, and design-system scope without claiming terminal verification.

## Expected result

The wrapper completes the focused unit-test task and the generated project remains free of machine-local state.

## Out of scope

Product scenarios, final navigation, emulator acceptance, and terminal Android verification remain outside this task.
