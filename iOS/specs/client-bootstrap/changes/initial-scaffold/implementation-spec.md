# Implementation spec — client bootstrap / iOS / initial scaffold

## Intake reference

Technical-only bootstrap with product impact assessed as NONE because only generated template behavior is introduced.

## Shared contract references

No shared product contract applies; this package establishes buildable infrastructure for later approved feature contracts.

## Platform requirements

### IOS-REQ-1 — Buildable iOS shell

The repository contains an Xcode-discoverable iOS application target with SwiftUI sources and generated test targets.

## Platform acceptance criteria

### IOS-AC-1 — Focused Xcode build

The discovered application scheme builds successfully for an available iOS Simulator destination without relying on an open IDE session.

`Covers: IOS-REQ-1`

## Constraints

Generated local state, signing material, Derived Data, and user-specific Xcode configuration remain outside version control.

## Integration points

The Xcode project owns the application, unit-test, and UI-test targets together with the generated asset and persistence resources.

## Open questions

None.
