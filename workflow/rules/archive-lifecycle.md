# Archive lifecycle

Archive is collision-safe, has no overwrite or force mode, and always runs a
dry-run before explicit `--apply`.
Exact targets use lexical `lstat`/`lexists` collision checks, so dangling
symlinks are collisions. Every existing archive-namespace ancestor must be a
real directory inside the repository: symlink and non-directory ancestors block
before mutation, and parent creation rechecks the same chain without following
an unsafe existing path. This applies equally to implementation and product
archives.

Active implementation/product source trees are self-contained: every recursive
entry must be a real directory or regular file. Symlinks, sockets, FIFOs,
devices and other special nodes block before any lifecycle validator follows or
reads them. The integrity builder applies the same recursive `lstat` contract,
so an archive manifest never hashes through an external link.

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
relocation, atomically publishes the verified full post-change contract as
`<platform>/specs/<feature>/SPECIFICATION.md`, writes a versioned
`archive-receipt.json`, and leaves
`changes/<change-id>/ARCHIVED.md` with the exact destination. A collision or
partial failure rolls back; the shared source is never modified.

`SPECIFICATION.md` is the durable current baseline for future Propose/Plan and
is not a change package or tombstone. It contains provenance to the immutable
archived `implementation-spec.md`, its SHA-256 and the receipt. Receipt schema
version 2 binds the archived source and the bytes published at archive time;
historical version 1 receipts remain valid. A later archive may replace the
current baseline without invalidating an older receipt. Existing baseline
replacement is atomic; failure restores its exact prior bytes or absence.
For `product-backed`, the durable header also points to
`specs/product/<feature>/SPECIFICATION.md` as the current product contract and
states the lifecycle transition explicitly: before `archive product completed`,
the implementation archive's copied shared provenance remains the immutable
evidence; after it, the product baseline is the future-agent entrypoint.
`technical-only` never fabricates a shared-product link.

The receipt is the implementation archive proof. Receipt/archive ancestors,
receipt, `meta.json`, verification state and every manifest entry must remain
self-contained regular non-symlink paths. Schema versions 1 and 2 bind
platform, feature, change ID, terminal task counts, PASS verification state and
its original fingerprint to a SHA-256 manifest of the archived package; v2
additionally binds durable specification publication. The
manifest excludes only the exact root `<archive>/archive-receipt.json`; nested
files with the same basename remain integrity-bound. Version 2 also excludes
non-contractual macOS `.DS_Store` metadata. Version 1 validation preserves its
recorded semantics: if its manifest listed `.DS_Store`, that file remains
integrity-bound; if it did not, later stray `.DS_Store` is ignored for
compatibility. Any later integrity-bound package mutation makes the receipt invalid.

Rollback restores the exact pre-call tree for failures before or after move.
Only archive parent directories created by the current call may be removed, and
only while empty; pre-existing directories are preserved.

## Implementation retirement

`archive implementation <platform> <feature> [--change <change-id>] --retire
superseded|cancelled` explicitly retires a non-terminal platform package that
cannot honestly become `verified`. It requires a valid
`specified|planned|implementing` package in its current lifecycle mode, rejects
`verified`/`PASS` packages, runs the same collision, no-symlink and rollback
guards as a verified implementation archive, then moves the package to:

```text
<platform>/specs/<feature>/archive/<YYYY-MM-DD-change-id>/
```

Apply writes archived metadata with `status: archived`, `retirement_reason` and
`retired_status`, emits root `archive-receipt.json` with
`mode: implementation-retirement`, and leaves the active
`changes/<change-id>/ARCHIVED.md` tombstone. It never publishes, creates or
rewrites durable `<platform>/specs/<feature>/SPECIFICATION.md`; any previous
delivered baseline is preserved byte-for-byte and absence remains absence.

The retirement receipt is integrity-bound to the archived package and is valid
only for active tombstone classification, ownership unblocking and historical
traceability. It is deliberately not a delivered implementation proof:
`archive product completed` and any platform disposition
`disposition: archived` continue to require a verified implementation archive
receipt. Product `superseded`/`cancelled` may cite cancelled/not-applicable
narrative evidence separately, but must not treat an implementation retirement
receipt as delivery evidence.

## Product archive

`archive product <feature>` consumes a validated retirement request based on
[`product-archive-request.json`](../templates/product-archive-request.json).
Canonical default request находится вне active product fingerprint:
`specs/product/_retirement-requests/<feature>/<YYYY-MM-DD-feature>.json`.
Optional `--request <repo-relative-path>` выбирает другой safe regular JSON,
но path обязан находиться вне active product package и не ослабляет exact
schema и approval/disposition gates. Internal request блокируется до mutation,
даже если receipt был пересчитан с ним в fingerprint.
Default и explicit request проверяются по lexical repo-relative identity до
чтения: все существующие ancestors — реальные directories, сам request —
bounded regular non-symlink file. Symlink request/parent, traversal, external
absolute path и special node блокируются без resolve/follow.
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
or a tombstone-only directory whose exact archive target has a valid verified
archive receipt or implementation retirement receipt. Partial directories,
extra tombstone files, broken targets and `archived` meta under active changes
block product archive.

Apply moves the complete product package to
`specs/product/_archive/<feature>/<YYYY-MM-DD-feature>/`. For `completed`, it
atomically publishes the approved full product contract as
`specs/product/<feature>/SPECIFICATION.md`; for `superseded`/`cancelled`, it
preserves the previous baseline exactly and never promotes the retired
candidate (if no previous baseline exists, none is fabricated). It also
recreates the exact active `specs/product/<feature>/spec.md` tombstone with `Status: ARCHIVED`,
reason, target, approver and evidence. Platform packages are never rewritten.
Validated request копируется в target как exact `retirement-request.json` и
становится durable retirement evidence. Ошибка copy/tombstone вызывает полный
rollback; request source и platform archives остаются неизменными.
Active package не может заранее содержать reserved `retirement-request.json`.
Durable copy записывается через atomic temp+replace; rollback удаляет созданные
durable/temp/tombstone paths до reverse move и восстанавливает exact tree,
включая прежний `SPECIFICATION.md`. Symlink, directory и иная non-regular
collision на baseline/source блокируют apply до mutation.
The `_archive` namespace is excluded from active product discovery.
