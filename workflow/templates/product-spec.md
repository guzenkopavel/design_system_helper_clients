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

- `AC-1` — <one observable outcome>. `Covers: REQ-1`

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

## Common Product Constraints

## Open Questions

Для `READY` здесь не должно быть блокирующих вопросов.

## Readiness Decision

`READY` разрешён только при полном REQ↔AC coverage, свежем static-linked
`review-verdicts.json` со статусом PASS и six isolated PASS/valid N/A, готовом `ux.md` для
UI/interaction scope, закрытых blockers и явном `Product approval: APPROVED` с
approver/evidence. Каждое critical metadata поле и каждый REQ/AC ID должны быть
уникальны. GAP/UNKNOWN findings сохраняются в durable non-green receipt, но не
разрешают READY. Findings живут в receipt, а не копируются сюда.
