---
phase: plan
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/plan/README.md
  - <platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md
requires_verification: focused
recommended_roles:
  - repo-navigator
  - implementation-planner
---

# Phase: Plan

Form: `plan <platform> <feature> [--change <change-id>]`. Resolve an omitted
change only when exactly one active package exists. Ambiguity, missing adapter
or unsafe slug blocks before writes.

Require a valid `specified` package with matching platform/feature/change,
closed blockers and passed design gate. `repo-navigator` and the platform guard
are read-only; `implementation-planner` is the sole owner of `plan/`.

Create a DAG of contiguous self-contained `task-NNN.md` files. Each task has one
layer, no more than two ideal days, explicit existing/proposed paths, inline
REQ/AC context, dependencies, focused verification, expected result and
out-of-scope. Machine fields begin as `Status: pending` and `Evidence: none`.
UI tasks include adapter runtime, accessibility and design-system checks.

Candidate meta is `planned`, `tasks_total` equals the derived file count,
`tasks_done: 0`, verification remains pending. Validate with `--mode plan
--change`. On failure return to `specified`, reset counts and report blockers.
Do not change contracts for planning convenience, write production code or
commit.
