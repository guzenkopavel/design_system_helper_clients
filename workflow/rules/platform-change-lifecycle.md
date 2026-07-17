# Platform change lifecycle

Adapter `lifecycle_capabilities` is a canonical ordered prefix/dependency set:
plan requires propose, implement requires plan, verify requires implement, and
implementation archive requires verify. Unsupported operations fail before
package discovery or writes. Phase profiles and applicable rule union include
only supported engineering phases. Product archive is a separate shared flow.

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

Adapter `rule_files` is a catalog. Exact `phase_rule_profiles` and
`scope_rule_profiles` select what each lifecycle phase reads. Propose records
evidence-selected scopes; Plan may refine/add before `planned`; downstream
phases cannot invent scopes.

Adapter `modularity` declares `contract_version: 1`, names the isolation scope,
platform-owned non-application physical-unit rule/unit kinds and v0 legacy task
checks. Common+platform modularity rules are mandatory in every
Propose/Plan/Implement/Verify base profile; they do not depend on selecting the
isolation scope. The scope becomes mandatory when design outcome is `isolated`.

Required `meta.json` fields are `platform`, `feature`, `change_id`,
`change_type`, `tier`, `status`, `shared_product_spec`, `product_status`,
`product_approval`, `product_impact`, `impact_evidence`, `blocking_questions`,
`engineering_scopes`, `applicable_rule_files`, `problems`, `design_gate`,
`tasks_total`, `tasks_done`, `verification_status`, `verified_at` and
`verification_state` and `modularity_contract_version`. The rule list is the exact deterministic union of all
lifecycle phase bases and selected scope profiles; unknown, missing, extra or
unsafe paths are invalid.
At `planned`, Plan seals both arrays in fingerprinted
`plan/rule-selection.json`, so Implement/Verify cannot change selection without
returning to Plan. Design must cover every selected scope exactly once with a
decision or explicit N/A rationale and also contain exact structured
`Modularity decision` plus `Boundary guard verdict: PASS`. Tasks declare scope
subsets and a substantive boundary owner; their union covers the sealed package
scopes and activates adapter conditional checks.

Missing `modularity_contract_version` is interpreted as legacy v0 only for a
`planned|implementing|verified` package whose exact identity and immutable
structure match [`modularity-v0.json`](../compatibility/modularity-v0.json).
Its historical phase projection and adapter-declared legacy isolation checks
stay valid for Implement/Verify/Archive. Propose/Plan, registry mismatch and any
reconcile that expands v0 design/plan/scopes/tasks are blocked and route to an
explicit new migration/change package. Only task `Status`/`Evidence` values,
corresponding lifecycle meta fields and new evidence may advance normally. New
packages always use v1; unsupported versions fail.
Common resolver также требует exact legacy meta keys и code-pinned digest всего
registry/exact two identities. `blocking_questions`, `tasks_total`, extra keys
и registry-only extension являются immutable drift.

The v1 snapshot is a deterministic consistency lock for current packages. The
tracked v0 registry is a separate compatibility trust anchor for the two named
historical identities; changing it requires an explicit harness change and
fresh audit.

The only pre-delivery exception to downstream package immutability is explicit
[`reconcile-implementation`](implementation-reconciliation.md). Its guard may
repair the selected package for an explicit production path set without writing
production or shared behavior. It reopens affected/dependent tasks, invalidates
terminal evidence when required, validates in implement mode and still requires
a fresh Verify for terminal state.

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
- explicit implementation retirement may also move a valid
  `specified|planned|implementing` package to `archived` with
  `retirement_reason: superseded|cancelled`; this does not publish a durable
  platform baseline and cannot satisfy delivered-product archive evidence.

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
