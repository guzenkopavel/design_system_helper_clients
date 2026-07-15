# Proposal — client bootstrap / Android / initial scaffold

## Intake

This is a technical-only greenfield scaffold with no shared product contract and no observable product requirements.

## Goal

Establish a compilable Android application shell, Gradle wrapper, unit-test target, and resource structure for later feature work.

## Scope

Commit the generated application module, Compose entry point, theme resources, Gradle configuration, wrapper, and template tests.

## Engineering scope selection

Application, Compose, Gradle, and UI scopes cover the generated entry point, build graph, state-bearing UI shell, and emulator-facing resources.

## Applicable rule files

The exact lifecycle union is sealed in `meta.json` and `plan/rule-selection.json` for this bootstrap change.

## Non-goals

This change does not define training scenarios, product navigation, final architecture, branding, or terminal Android verification capability.

## Accepted decisions

Keep the generated scaffold intact as a disposable integration baseline while future changes replace template behavior through normal lifecycle tasks.

## Open questions

None.

## Risks

Template code may be mistaken for product behavior, so the package keeps product impact at NONE and terminal verification pending.
