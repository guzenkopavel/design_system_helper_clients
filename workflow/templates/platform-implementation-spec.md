# <Feature> — <iOS|Android> implementation specification

- **Direction:** `<iOS|Android>`
- **Change type:** `product-backed | technical-only`
- **Shared product spec:** `specs/product/<feature>/spec.md | NOT APPLICABLE`
- **Product status at intake:** `READY | N/A`
- **Product approval at intake:** `APPROVED | N/A`

Для `product-backed` обязательны путь, `READY` и `APPROVED`; не копируйте
product requirements и acceptance criteria, а ссылайтесь на их IDs.

Для `technical-only` значения могут быть `NOT APPLICABLE` / `N/A` только при
доказанном `Product impact assessment: NONE`.

## Product Impact Assessment

- **Result:** `NONE | PRESENT | UNCERTAIN`
- **Observable behavior evidence:** <почему пользовательское поведение не меняется>
- **Requirements evidence:** <почему product REQ не меняются>
- **Acceptance criteria evidence:** <почему product AC не меняются>

`technical-only` разрешён только при `NONE` и заполненном evidence. При
`PRESENT` или `UNCERTAIN` остановиться и перейти в product elaboration; этот
режим не является обходом product gates для behavioral changes.

## Platform Scope

## Architecture and Design

## SDK, Framework and Module Decisions

## Platform Constraints

Если constraint конфликтует с product intent, верните вопрос в shared product
spec вместо локального переопределения.

## Requirement-to-Test Traceability

| Product requirement | Platform tests | Coverage status |
|---|---|---|

## Implementation Plan

## Migration and Rollout

## Risks and Open Questions
