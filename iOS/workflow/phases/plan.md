# iOS addendum: Plan

Plan lives under `iOS/specs/<feature>/changes/<change-id>/plan/` and uses
`IOS-REQ-N`/`IOS-AC-N` inline context. Apply the adapter rule files based on task
scope. Domain precedes data and presentation; build wiring is infrastructure.

Every UI task includes simulator, accessibility, design-system and localization
verification. Xcode configuration names must be discovered, never invented.
Apple SDK and concurrency risks receive explicit checkpoints.
