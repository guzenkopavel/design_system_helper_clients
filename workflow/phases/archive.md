---
phase: archive
writes_artifacts:
  - platform archive package, durable SPECIFICATION.md and ARCHIVED.md tombstone
  - product archive package, durable SPECIFICATION.md and spec.md tombstone
requires_verification: terminal
recommended_roles: []
---

# Phase: Archive

Public forms:

- `archive implementation <platform> <feature> [--change <change-id>]`
- `archive implementation <platform> <feature> [--change <change-id>] --retire superseded|cancelled`
- `archive product <feature>`

Product form по умолчанию читает
`specs/product/_retirement-requests/<feature>/<YYYY-MM-DD-feature>.json`; для
явного safe override CLI поддерживает `--request <repo-relative-path>`.
Override внутри active `specs/product/<feature>/` запрещён до mutation.

Both are deterministic, collision-safe and dry-run first. Verified
implementation mode requires validator `archive` success, then invokes
`archive-change.py implementation ... --apply`, preserves the original
verification fingerprint after relocation and emits `archive-receipt.json`; it
first requires `archive-implementation` capability. After apply, validate the
emitted receipt with `archive-change.py receipt --platform <platform>
--feature <feature> --receipt <repo-relative archive-receipt.json>`; this is the
post-archive integrity check, while `validate-platform-change --mode archive`
is the pre-apply active-package gate. Apply additionally
publishes the full verified post-change contract as feature-root
`SPECIFICATION.md` and binds its archived source/published bytes in receipt v2.
Implementation retirement mode requires explicit
`--retire superseded|cancelled` and a valid non-terminal
`specified|planned|implementing` package. It moves the package to the same
archive namespace, emits an `implementation-retirement` receipt, leaves
`ARCHIVED.md`, and never publishes or rewrites durable `SPECIFICATION.md`.
Retirement receipts only classify tombstones and unblock ownership; product
`archived` disposition still requires a verified implementation archive
receipt. Product mode is
capability-independent and requires a complete retirement
request, scans every adapter and conventional platform package root for active
references, then invokes `archive-change.py product ... --apply`. Apply сохраняет
validated request внутри product archive как `retirement-request.json`.
`completed` publishes the approved full product contract to the feature-root
`SPECIFICATION.md`; `superseded`/`cancelled` preserves the previous baseline and
never promotes the retired candidate.

Never overwrite, force, silently infer Android disposition, rewrite platform
packages or treat product approval as retirement approval. On failure, preserve
the pre-call state and report exact blockers.
