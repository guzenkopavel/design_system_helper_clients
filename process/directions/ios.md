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

Machine adapter: [`platform-contract.json`](../../iOS/workflow/platform-contract.json)
задаёт iOS name/root, production/protected roots, archive namespace, `IOS`
contract prefix, boundary guard и Extended gates;
общий validator не hardcode'ит эти значения.
