# iOS addendum: Propose

Package root is `iOS/specs/<feature>/changes/<change-id>/`; meta platform is
`iOS`, contract prefix is `IOS`, and placement review belongs to
[`ios-package-boundary-guard`](../roles/ios-package-boundary-guard.md).

Inspect real Xcode/package structure before design and never label a greenfield
path as existing. Always load architecture; conditionally load SDK pitfalls,
concurrency, unit/UI testing, accessibility, design-system, localization and
Xcode rules from the adapter. Extended design includes every configured section.
iOS-specific details never move into common or Android layers.
