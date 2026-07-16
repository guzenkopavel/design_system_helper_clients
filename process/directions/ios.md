# iOS direction

Корень: [`../../iOS/`](../../iOS/).

Здесь размещать только iOS-специфичные расширения: Xcode/build settings,
Swift/SwiftUI/UIKit conventions, Simulator и iOS UI automation. Общий контракт
дизайн-системы и процесса оставлять в `workflow/`.

Продуктовая спека находится в [`specs/product/`](../../specs/product/), а
iOS-специфика реализации — в [`iOS/specs/`](../../iOS/specs/). Реализация
в режиме `product-backed` ссылается на общий `READY`/`APPROVED`-контракт и не
переопределяет его. `technical-only` допускается без shared spec только при
доказанном `Product impact assessment: NONE`.

Публичные входы: `$propose ios <feature> [--change ...]`, `$plan`, `$implement`,
`$verify` и `$archive implementation`. Общий процесс
расширяется [`iOS/workflow/phases/`](../../iOS/workflow/phases/) и iOS rules;
активный пакет находится в `changes/<change-id>/` и проходит gates до каждого
lifecycle transition.

`$deep-code-review review|feedback|bug ios <feature> [--change ...]` подключает
iOS lens из platform addendum и остаётся read-only. Отдельный fix проходит
canonical Implement/reconcile lifecycle, после чего terminal evidence
маршрутизируется в `$verify ios ...`.

Machine adapter: [`platform-contract.json`](../../iOS/workflow/platform-contract.json)
задаёт iOS name/root, production/protected roots, archive namespace, `IOS`
contract prefix, boundary guard, modularity contract version и Extended gates;
phase/scope rule profiles, context file suffixes и полный catalog. Общий resolver/validator не
hardcode'ит эти значения. Common modularity и `package-development.md`
загружаются обязательным phase base; isolation scope `package` добавляет
task-level obligations только для `isolated|deviation`. Performance topics,
UI/simulator, concurrency, localization, delivery и DX загружаются только
выбранными scopes.

`pre_commit` profile этого adapter владеет iOS source, project, signing,
security, UI и localization globs. Общий gate не содержит Apple-specific
значений; iOS evidence трактуется по
[`pre-commit-check.md`](../../iOS/workflow/phases/pre-commit-check.md).

Product-backed `ui` добавляет sequential `ios-ux-designer` и `platform-ux.md`:
Liquid Glass availability, functional scope and older-OS fallback подтверждаются
repository evidence до architecture.
