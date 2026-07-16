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

Every proposal applies common modularity and `package-development.md` even when
the optional `package` scope is not yet selected. Inspect project/workspace,
target membership and manifests before choosing `isolated | deviation |
not-applicable`. New feature/data/network/storage/reusable UI capabilities use a
Swift package, Swift package target or non-application Xcode target by strong default; the app target remains
composition/lifecycle/root navigation/DI/config/resources only. `isolated`
selects `package`; the boundary guard returns structured `PASS|BLOCK` with exact
evidence and invalid/missing verdict blocks the design gate. Deviation may use
only an existing/discovered non-application unit and never the app target.

For product-backed `ui`, dispatch `ios-ux-designer` after specification writer.
It discovers SDK/deployment/components and owns only READY `platform-ux.md` with
Liquid Glass availability/fallback evidence before architecture starts.
