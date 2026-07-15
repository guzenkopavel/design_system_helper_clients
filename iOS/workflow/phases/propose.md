# iOS addendum: Propose

Package root is `iOS/specs/<feature>/changes/<change-id>/`; meta platform is
`iOS`, contract prefix is `IOS`, and placement review belongs to
[`ios-package-boundary-guard`](../roles/ios-package-boundary-guard.md).

Inspect real Xcode/package structure before design and never label a greenfield
path as existing. Resolve the `propose` base profile and evidence-selected
scopes (`application`, `ui`, `concurrency`, `performance`, `networking`,
`startup`, `memory`, `rendering`, `package`, `localization`, `xcode`, `simulator`, `delivery` or
`developer-experience`). Do not read the whole catalog by default. Architecture
and system-design are proposal-base; conditional rules load only through scopes.
Extended design includes every configured section.
iOS-specific details never move into common or Android layers.
