# iOS design-system integration

До выбора компонента найти существующие tokens/primitives/components в реальном
iOS source. Не выдумывать название API. Новый reusable primitive допустим только
после доказанного gap; feature code не дублирует token values и shared styling.

Design фиксирует semantic role, state variants, accessibility и fallback.
Verification включает simulator comparison для layout/color/typography/hit area
и проверку light/dark/large text, если они поддерживаются клиентом.

## Component contract

- Tokens выражают роль (`primaryText`, `criticalAction`), а не случайное значение.
- Component описывает states: default, pressed/focused, disabled, loading, error,
  empty и content overflow — только применимые к его контракту.
- Feature не обходит component API локальными color/font/spacing literals.
- Новый variant добавляется после проверки существующего extension point и
  потребителей; one-off composition не превращается автоматически в primitive.
- UIKit/SwiftUI bridge сохраняет semantics, state ownership и Dynamic Type.

Source of truth может быть code, generated assets или внешний design contract —
его нужно обнаружить. Названия токенов, platform appearance features и
минимальная OS не предполагаются. Visual comparison дополняет, но не заменяет
behavior/accessibility assertions.

## Liquid Glass adaptation

Для product-backed `ui` package создать `platform-ux.md` по общему template.
Сначала обнаружить реальный SDK, deployment target и существующие компоненты.
Liquid Glass применять system-first только в функциональном слое controls и
navigation, не как content background. Не переиспользовать glass повсеместно и
не создавать custom effects без доказанного gap. Soft-blue tint ограничен
semantic roles. Зафиксировать light/dark/increased contrast, Reduce
Transparency, Reduce Motion, scrolling legibility, standard components,
performance и явный older-OS/SDK fallback. Доступность API не предполагать.
Contract terms: functional controls; Reduce Transparency; Reduce Motion.

Official references:
- https://developer.apple.com/documentation/TechnologyOverviews/adopting-liquid-glass
- https://developer.apple.com/design/human-interface-guidelines/materials
