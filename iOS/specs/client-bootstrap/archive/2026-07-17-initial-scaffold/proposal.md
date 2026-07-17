# Proposal — client bootstrap / iOS / initial scaffold

## Intake

This is a technical-only greenfield scaffold with no shared product contract and no observable product requirements.

## Goal

Establish a compilable iOS application shell, Xcode project, unit-test target, UI-test target, and initial asset structure.

## Scope

Commit the generated SwiftUI entry point, persistence template, assets, Core Data model, Xcode project, and template tests.

## Engineering scope selection

Application, UI, and Xcode scopes cover the generated composition entry point, simulator-facing shell, targets, and build configuration.

## Applicable rule files

The exact lifecycle union is sealed in `meta.json` and `plan/rule-selection.json` for this bootstrap change.

## Non-goals

This change does not define training scenarios, final architecture, navigation, branding, accessibility acceptance, or product UI behavior.

## Accepted decisions

Keep the generated scaffold intact as a disposable integration baseline while later feature changes replace template behavior through normal lifecycle tasks.

## Open questions

None.

## Risks

Template code may be mistaken for product behavior, so the package keeps product impact at NONE and terminal verification pending.
