# <Feature> — shared product specification

- **Status:** `DRAFT | READY`
- **Product approval:** `PENDING | APPROVED`
- **Approved by:** `<person or role; required for READY>`
- **Approval evidence:** `<explicit decision reference; required for READY>`
- **Applies to:** `iOS, Android`
- **Source brief:** `brief.md`
- **UX artifact:** `ux.md | NOT APPLICABLE: <reason>`
- **Product review receipt:** `review-verdicts.json`
- **UX readiness:** `review-verdicts.json#ux-accessibility`

## Problem and Why

## Outcomes and Success Signals

## Scope

## Non-Goals

## Product Decisions

## Shared Observable Behavior

### Happy path

### Secondary states

Опишите применимые loading, empty, error, offline, accessibility,
localization, analytics и privacy outcomes.

## Requirements

- `REQ-1` — <observable product requirement>

## Acceptance Criteria

- `AC-1` — <один наблюдаемый outcome>. `Covers: REQ-1` `Verification dimension: <unique-kebab-case>`

## Requirement Coverage

| Requirement | Acceptance criteria |
|---|---|
| `REQ-1` | `AC-1` |

## Client Readiness

| Check | iOS | Android | Evidence or gap |
|---|---|---|---|
| Happy path | PASS/GAP | PASS/GAP | |
| Secondary states | PASS/GAP | PASS/GAP | |
| Product intent parity | PASS/GAP | PASS/GAP | |
| Atomic evidence obligations | PASS/GAP | PASS/GAP | |

Client Readiness оценивает полноту shared product contract отдельно для iOS и
Android. Это не статус platform implementation, build или runtime verification.

## Common Product Constraints

## Open Questions

Для `READY` значение должно быть exact `None.`.

## Readiness Decision

- **Decision:** `DRAFT | READY`
- **Blocking reasons:** `<причины> | none`

Для terminal `READY` нужны exact `Decision: READY` и `Blocking reasons: none`.
Каждый AC задаёт ровно один наблюдаемый outcome и одну уникальную
`Verification dimension`; appearance, assistive semantics, text scaling,
light/dark и increased contrast не объединяются в один AC/evidence obligation.
`DRAFT`, `PENDING`, `GAP` или `UNKNOWN` в Client Readiness, Open Questions либо
Readiness Decision противоречат READY и блокируют fan-out.
