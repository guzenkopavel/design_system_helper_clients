---
phase: archive
writes_artifacts:
  - platform archive package and ARCHIVED.md tombstone
  - product archive package and spec.md tombstone
requires_verification: terminal
recommended_roles: []
---

# Phase: Archive

Public forms:

- `archive implementation <platform> <feature> [--change <change-id>]`
- `archive product <feature>`

Both are deterministic, collision-safe and dry-run first. Implementation mode
requires validator `archive` success, then invokes `archive-change.py
implementation ... --apply`, preserves the original verification fingerprint
after relocation and emits `archive-receipt.json`. Product mode requires a complete retirement
request, scans every adapter and conventional platform package root for active
references, then invokes `archive-change.py product ... --apply`.

Never overwrite, force, silently infer Android disposition, rewrite platform
packages or treat product approval as retirement approval. On failure, preserve
the pre-call state and report exact blockers.
