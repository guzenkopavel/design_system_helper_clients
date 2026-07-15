# iOS addendum: Propose

Применять после общей [`propose`](../../../workflow/phases/propose.md) и adapter
[`platform-contract.json`](../platform-contract.json).

## Concrete contract

- package root: `iOS/specs/<feature>/`;
- `meta.platform`: `iOS`;
- platform IDs: `IOS-REQ-N` и `IOS-AC-N`;
- read-only boundary role:
  [`ios-package-boundary-guard`](../roles/ios-package-boundary-guard.md).

До design проверить текущую Xcode/project/package структуру. Proposed greenfield
path нельзя объявлять существующим.

## Conditional rule loading

- Всегда: [`architecture.md`](../rules/architecture.md).
- При networking/file system/UIKit/Foundation или другом Apple SDK scope:
  [`ios-pitfalls.md`](../rules/ios-pitfalls.md).
- При task/actor/lock/MainActor/Sendable scope:
  [`swift-concurrency.md`](../rules/swift-concurrency.md).
- При unit verification:
  [`unit-testing.md`](../rules/unit-testing.md).
- При UI behavior/automation:
  [`ui-testing.md`](../rules/ui-testing.md) и
  [`ui-test-spec.md`](../rules/ui-test-spec.md).
- При UI scope: [`accessibility.md`](../rules/accessibility.md) и
  [`ui-design-system.md`](../rules/ui-design-system.md).

Extended design содержит substantive sections `System-design review`,
`Apple SDK considerations`, `Concurrency model`, `Platform verification gates`.
UI scope требует simulator plan, VoiceOver/Dynamic Type и identifiers отдельно
от accessibility labels. iOS rules не переносить в common или Android.
