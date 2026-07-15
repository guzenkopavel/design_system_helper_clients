# Platform change lifecycle

## Identity and layout

Platform implementation identity is the tuple `platform + feature + change_id`.
Both `feature` and `change_id` are strict kebab-case slugs. Active packages live
only at:

```text
<platform>/specs/<feature>/changes/<change-id>/
```

Archived packages live at:

```text
<platform>/specs/<feature>/archive/<YYYY-MM-DD-change-id>/
```

There is no legacy fallback to `<platform>/specs/<feature>/meta.json`.
`propose` defaults a new omitted `--change` to the feature slug. Downstream
commands may omit `--change` only when discovery finds exactly one active
package. Zero or multiple active packages is a blocker before writes. A changes
directory containing only `ARCHIVED.md` is a tombstone, not an active package.

## Package

An active package contains `meta.json`, `proposal.md`,
`implementation-spec.md`, `design.md`, `verification.md`, `plan/README.md`,
contiguous `plan/task-NNN.md` files and, after implementation begins, `evidence/`.
The selected platform adapter supplies roots, contract prefix, production and
protected paths, platform rules and archive namespace.

Required `meta.json` fields are `platform`, `feature`, `change_id`,
`change_type`, `tier`, `status`, `shared_product_spec`, `product_status`,
`product_approval`, `product_impact`, `impact_evidence`, `blocking_questions`,
`problems`, `design_gate`, `tasks_total`, `tasks_done`, `verification_status`,
`verified_at` and `verification_state`.

Allowed statuses are `draft`, `specified`, `planned`, `implementing`, `verified`
and `archived`. `tasks_total` and `tasks_done` are derived from task files and
must never be trusted as authoritative input. `verification_status` is
`pending`, `PASS`, `FAIL` or `UNKNOWN`.

## Transitions

```text
draft → specified → planned → implementing → verified → archived
```

- `specified` requires complete propose artifacts, closed blockers, REQ↔AC
  coverage and a content-derived design gate.
- `planned` requires a valid DAG and contiguous tasks. Every task begins with
  `Status: pending` and `Evidence: none`.
- `implementing` begins only from `planned`; it never implies verification.
- a task becomes `done` only after focused evidence exists. A done task whose
  dependency is not done is invalid.
- `verified` is assigned only by fresh `$verify`; every active verification row
  must be exact `PASS`, concrete evidence must exist and the state fingerprint
  must match current code and contracts.
- `archived` is written only by collision-safe archive apply after all terminal
  gates pass.

A failed Verify persists a recoverable `implementing` state: FAIL takes
precedence over UNKNOWN, `problems` exactly matches non-PASS contract IDs,
affected tasks reopen to pending/none and `tasks_done` is rederived. No mapped
task means plan repair, not inferred scope.

Any invalid candidate transition is rolled back to its prior valid status.

## Tier and contract separation

Tier semantics remain `quick`, `standard`, `extended`. Quick design can be
not-applicable only with a bounded reason; Standard requires common design;
Extended loads all system-design and platform gates.

Shared `REQ-*`/`AC-*` remain only in `specs/product/<feature>/spec.md`.
Product-backed packages reference the exact active shared path and require
`READY` plus explicit `APPROVED` evidence. Technical-only packages require
`Product impact assessment: NONE` with evidence. Platform constraints that
change observable behavior return to product elaboration.

Verification and archive rules are canonical in
[`verification-evidence.md`](verification-evidence.md) and
[`archive-lifecycle.md`](archive-lifecycle.md).
