# iOS design-system integration

До выбора компонента найти существующие tokens/primitives/components в реальном
iOS source. Не выдумывать название API. Новый reusable primitive допустим только
после доказанного gap; feature code не дублирует token values и shared styling.

Design фиксирует semantic role, state variants, accessibility и fallback.
Verification включает simulator comparison для layout/color/typography/hit area
и проверку light/dark/large text, если они поддерживаются клиентом.
