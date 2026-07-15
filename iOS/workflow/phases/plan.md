# iOS addendum: Plan

Применять после общей [`plan`](../../../workflow/phases/plan.md) и adapter
[`platform-contract.json`](../platform-contract.json).

## Concrete contract

- package root: `iOS/specs/<feature>/`;
- inline platform IDs: `IOS-REQ-N` + `IOS-AC-N`;
- placement review:
  [`ios-package-boundary-guard`](../roles/ios-package-boundary-guard.md).

## Conditional rule loading

- Любая Swift implementation task:
  [`architecture.md`](../rules/architecture.md).
- Apple SDK integration: [`ios-pitfalls.md`](../rules/ios-pitfalls.md).
- Concurrency task: [`swift-concurrency.md`](../rules/swift-concurrency.md).
- Unit/test task: [`unit-testing.md`](../rules/unit-testing.md).
- UI task: [`ui-testing.md`](../rules/ui-testing.md),
  [`ui-test-spec.md`](../rules/ui-test-spec.md),
  [`accessibility.md`](../rules/accessibility.md),
  [`ui-design-system.md`](../rules/ui-design-system.md).

Domain → Data → Presentation; UI не ставить раньше contracts/stubs. UseCase
tasks inline включают релевантный checklist из
[`architecture/use-cases.md`](../rules/architecture/use-cases.md), Presentation
tasks — из [`architecture/mvvm.md`](../rules/architecture/mvvm.md).

Каждая UI task содержит simulator, accessibility и design-system verification.
Xcode target/package/project wiring выделять в infrastructure layer. Apple SDK
и concurrency risks получают checkpoint. App Store review при применимости
указывается отдельным календарным диапазоном.
