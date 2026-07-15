# Archive lifecycle

Archive is collision-safe, has no overwrite or force mode, and always runs a
dry-run before explicit `--apply`.

## Implementation archive

`archive implementation <platform> <feature> [--change <change-id>]` requires
the exact package identity, `status: verified`, all contiguous tasks `done`, no
blocking questions or problems, exact `PASS` verification rows with existing
evidence, and a fresh state fingerprint. Product-backed packages additionally
require the referenced shared product spec to remain `READY`/`APPROVED`.

Apply moves the package to
`<platform>/specs/<feature>/archive/<YYYY-MM-DD-change-id>/`, records archived
metadata, copies the shared spec into immutable `provenance/` when
product-backed, validates the original verification fingerprint after
relocation, writes a versioned `archive-receipt.json`, and leaves
`changes/<change-id>/ARCHIVED.md` with the exact destination. A collision or
partial failure rolls back; the shared source is never modified.

The receipt is the implementation archive proof. Schema version 1 binds
platform, feature, change ID, terminal task counts, PASS verification state and
its original fingerprint to a SHA-256 manifest of the archived package. The
manifest excludes only the receipt itself. Any later package mutation makes the
receipt invalid.

Rollback restores the exact pre-call tree for failures before or after move.
Only archive parent directories created by the current call may be removed, and
only while empty; pre-existing directories are preserved.

## Product archive

`archive product <feature>` consumes a validated retirement request based on
[`product-archive-request.json`](../templates/product-archive-request.json).
`READY`/`APPROVED` is not retirement authorization. The request requires reason,
explicit approver and evidence, plus a disposition with evidence for every
platform in `Applies to`. Missing Android adapter or disposition is never
treated as success.

`completed` requires the active product spec itself to remain `READY` with
explicit `Product approval: APPROVED`, concrete approver/evidence, and every
applicable disposition `archived`. An `archived` disposition is valid only when
its evidence is a safe repo-relative path to an existing conventional
`<Platform>/specs/<feature>/archive/<archive-id>/archive-receipt.json`.
Directories, `meta.json`, narrative, tombstone, active-change, absolute and
traversal evidence are rejected. Receipt, archived meta, verification state and
integrity manifest must agree; no current adapter is required to validate a
historical platform archive.
`superseded`/`cancelled` may use explicit `cancelled` or `not-applicable`
evidence and may retire a draft product package with separate retirement
approval. Any active implementation reference blocks all reasons.

Reference discovery merges adapter-defined `package_root`/active namespace with
conventional `*/specs/<feature>/changes/` roots. Every active-namespace child is
classified fail-closed: it must be either a valid active package with `meta.json`
or a tombstone-only directory whose exact archive target has a valid receipt.
Partial directories, extra tombstone files, broken targets and `archived` meta
under active changes block product archive.

Apply moves the complete product package to
`specs/product/_archive/<feature>/<YYYY-MM-DD-feature>/` and recreates only the
exact active `specs/product/<feature>/spec.md` tombstone with `Status: ARCHIVED`,
reason, target, approver and evidence. Platform packages are never rewritten.
The `_archive` namespace is excluded from active product discovery.
