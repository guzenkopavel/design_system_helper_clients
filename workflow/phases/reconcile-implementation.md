---
phase: reconcile-implementation
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/implementation-spec.md
  - <platform>/specs/<feature>/changes/<change-id>/design.md
  - <platform>/specs/<feature>/changes/<change-id>/verification.md
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
  - <platform>/specs/<feature>/changes/<change-id>/plan/
  - <platform>/specs/<feature>/changes/<change-id>/evidence/reconciliation-*.md
requires_verification: focused-and-implement-validator
recommended_roles:
  - implementation-discovery
  - specification-writer
  - architecture-designer
  - implementation-planner
  - implementation-writer
---

# Phase: Reconcile Implementation

Form: `reconcile-implementation <platform> <feature> [--change <change-id>]
--path <repo-relative>...`. Run once per platform package identity before staging. Receive the
intended production paths explicitly from the user/coordinator; never expand
them to all dirty files. Different feature/change IDs on the same platform use
separate calls, guards and reports.

Каждый intended path проходит тот же canonical lexical/canonical ownership
helper, что Plan и Implement: protected/excluded overlap и symlink file,
directory либо proposed-child traversal дают route до guard writes.
Canonical change-entry helper разделяет `identity_paths`, `mutable_paths` и
`read_only_copy_sources`: rename old/new mutable, у copy mutable только
destination, а unchanged source остаётся guarded read-only. Обе стороны copy
обязательны в intended и reconciliation evidence.

First run the canonical script in `inspect` mode. `implementation-discovery`
then compares the explicit production diff with shared behavior, platform
contracts/design, task coverage and current evidence. Classify it as `aligned`,
`task-drift`, `platform-implementation-drift`, shared behavior present or
uncertain. An adapter-owned uncovered path is `task-drift` or
`platform-implementation-drift`, not a blocker. Add/repair its coherent task and
evidence. Shared/uncertain routes to Discovery/Elaborate with zero writes.

Route `draft` to Propose, `specified` to Plan, `FAIL`/`UNKNOWN` to canonical
`$implement` recovery, and archived state to a new change — all before guard
writes. `planned` may start but a successful result must become `implementing`;
an `implementing` baseline must remain `implementing`.

For a supported class, run `start` with that exact classification. Use the
canonical owners only: specification writer for platform spec/verification,
architecture designer for design, implementation planner for coherent tasks and
selection snapshot, and implementation writer in `platform-reconciliation`
mode for package state and fresh evidence. No role may write production,
proposal, shared product, rules, adapters or historical evidence.

Reopen affected tasks and transitive dependents, run focused checks against the
explicit paths, then create new unique reconciliation evidence and complete only
the tasks proven by it. Evidence for every dependent names the complete
triggering intended path set and has exactly one `- Result: PASS` field.
Authored prose в exact direct-child canonical
`evidence/reconciliation-<timestamp>-task-NNN[-<safe-slug>].md` писать по-русски
по [`artifact-language`](../rules/artifact-language.md). Raw runtime/verifier
output и произвольные evidence files не переводить и не использовать как
language padding.
Any Result-like structural variant makes evidence invalid; ordinary narrative
without a Result field definition is unaffected. Full task-file add/change/delete,
including status/evidence, is restricted to baseline/current direct owners and
their transitive dependent closure. Semantic hashes separately prove actual
drift repair. Для current v1 `aligned` сохраняет `Implementation deliverables`
byte-for-byte; task/platform drift может согласованно уточнить список, но
финальная task обязана сохранить минимум два конкретных top-level list item
отдельно от `Steps` и `Expected result`. Invalidate prior verified state exactly; never
clear FAIL/UNKNOWN recovery. Apply the rule's per-class meta allowlist. Finish with `check <token>`, which includes the
platform validator in implement mode.

`start` binds the guard to a scoped lane projection: selected package/intended
paths/read dependencies/control plane и exact projected index. `check` rejects
selected-lane drift, но принимает disjoint package/product/platform changes и
unrelated commits. Runtime reconciliation still never stages;
fixture-only end-to-end tests may stage only after a successful `check` to prove
the canonical pre-commit gate accepts the reconciled production/package set.

Return a pre-staging report with classification, identity, intended paths,
affected/reopened tasks, package writes, commands/results, final validator and
next route. A previously verified package needs fresh `$verify` to restore its
terminal claim; a non-terminal package may proceed to scoped staging/pre-commit
after `RECONCILED`. Do not stage, commit or push.
