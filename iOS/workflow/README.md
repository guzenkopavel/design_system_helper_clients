# iOS workflow addenda

Общий lifecycle находится в [`../../workflow/`](../../workflow/). Здесь живут
только iOS phase addenda, boundary role и Apple/Swift engineering corpus.

## Phase addenda

- [`phases/propose.md`](phases/propose.md)
- [`phases/plan.md`](phases/plan.md)
- [`phases/implement.md`](phases/implement.md)
- [`phases/verify.md`](phases/verify.md)
- [`phases/archive.md`](phases/archive.md)

## Rule profiles

[`platform-contract.json`](platform-contract.json) содержит полный catalog,
exact base для четырёх engineering phases и selective scopes. Resolver загружает
только base текущей фазы плюс scopes из package meta; flat catalog не является
глобальным context.

- application/package architecture: [`rules/architecture.md`](rules/architecture.md)
- Swift/application/package: [`rules/swift-style.md`](rules/swift-style.md),
  [`rules/app-development.md`](rules/app-development.md),
  [`rules/package-development.md`](rules/package-development.md)
- UI/runtime: [`rules/ui-design-system.md`](rules/ui-design-system.md),
  [`rules/accessibility.md`](rules/accessibility.md),
  [`rules/ui-testing.md`](rules/ui-testing.md),
  [`rules/simulator.md`](rules/simulator.md)
- concurrency: [`rules/swift-concurrency.md`](rules/swift-concurrency.md)
- performance: [`rules/performance.md`](rules/performance.md)
- integration: [`rules/localization.md`](rules/localization.md),
  [`rules/xcode.md`](rules/xcode.md), [`rules/ios-pitfalls.md`](rules/ios-pitfalls.md)

Actual targets, schemes, compiler settings, runtimes and commands are discovered
from repository configuration. Greenfield defaults remain provisional.
