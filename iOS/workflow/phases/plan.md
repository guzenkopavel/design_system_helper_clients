# iOS addendum: Plan

Plan lives under `iOS/specs/<feature>/changes/<change-id>/plan/` and uses
`IOS-REQ-N`/`IOS-AC-N` inline context. Resolve the exact plan profile plus stored
scopes; refine/add scopes only before candidate `planned` and recompute the
lifecycle union. Domain precedes data and presentation; build wiring is
infrastructure.

Every UI task includes simulator, accessibility and design-system verification.
Localization checks are added only when the separate `localization` scope is
selected. Xcode configuration names must be discovered, never invented.
Apple SDK and concurrency risks receive explicit checkpoints.
Package/network/performance tasks include discovered consumer/build commands,
measurement scenario and finite watchdog budgets where applicable.
Use the adapter's exact task obligations: package consumer/build, networking
cache/retry policy, concurrency cancellation/isolation, and the selected
performance-topic budget. Generic "performance covered" wording is insufficient.
