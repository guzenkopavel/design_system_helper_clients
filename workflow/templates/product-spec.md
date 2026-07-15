# <Feature> — shared product specification

- **Status:** `DRAFT | READY`
- **Product approval:** `PENDING | APPROVED`
- **Approved by:** `<person or role; required for READY>`
- **Approval evidence:** `<explicit decision reference; required for READY>`
- **Applies to:** `iOS, Android`
- **Source brief:** `brief.md`
- **UX artifact:** `ux.md | NOT APPLICABLE: <reason>`

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

## Product Review Lenses

| Lens | Applicability | Verdict | Findings or gaps |
|---|---|---|---|
| Product | REQUIRED | PASS/GAP | |
| UX/accessibility | REQUIRED/N/A + reason | PASS/GAP/N/A | |
| Design-system | REQUIRED/N/A + reason | PASS/GAP/N/A | |
| Data/analytics/privacy | REQUIRED/N/A + reason | PASS/GAP/N/A | |
| Security | REQUIRED/N/A + reason | PASS/GAP/N/A | |
| Cross-client parity | REQUIRED | PASS/GAP | |

## Common Product Constraints

## Open Questions

Для `READY` здесь не должно быть блокирующих вопросов.

## Readiness Decision

`READY` разрешён только при полном REQ↔AC coverage, `PASS` всех applicable
review lenses, готовом `ux.md` для UI/interaction scope, закрытых blockers и
явном `Product approval: APPROVED` с approver/evidence. Иначе зафиксировать
`DRAFT / PENDING APPROVAL` или конкретные gaps.
