---
phase: plan
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
  - <platform>/specs/<feature>/changes/<change-id>/plan/README.md
  - <platform>/specs/<feature>/changes/<change-id>/plan/rule-selection.json
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

Require `plan` capability before discovery. Revalidate selected engineering scopes against current evidence. Plan may add or
refine scopes before `planned`; it must recompute the exact lifecycle
`applicable_rule_files` union. After
`planned`, Implement/Verify cannot invent a scope. The sole pre-delivery repair
path is guarded `reconcile-implementation`, which must preserve shared behavior
and rebuild a coherent snapshot/task graph for its supported class. Record final selection and
evidence in plan README and seal the exact arrays/fingerprint in
`plan/rule-selection.json`; set meta `rule_selection_snapshot` to that path.
Disabled downstream phases do not enter the sealed union.
If a new scope lacks exact design coverage or invalidates an architecture decision,
return to Propose/architecture owner instead of editing design from Plan. Load
the exact plan profile and selected scope rules through
`find-platform-context.py --phase plan`.

Create a DAG of contiguous self-contained `task-NNN.md` files. Each task has one
layer, no more than two ideal days, explicit existing/proposed paths, inline
REQ/AC context, dependencies, focused verification, expected result and
out-of-scope. Each task declares a substantive `Boundary owner`. Machine fields
begin as `Status: pending` and `Evidence: none`.
UI tasks include adapter runtime, accessibility and design-system checks.
Product-backed UI tasks also reference `platform-ux.md` and include every
adapter `platform_ux.task_checks` native appearance/fallback check.
Tasks translate applicable code/TDD/test/performance rules into concrete paths,
commands, budgets and expected evidence. Nontrivial test commands receive
explicit watchdog max/stall/output limits; commands are discovered, not guessed.
Every task declares a sorted JSON `Engineering scopes` subset of the sealed
package scopes. Together tasks cover every selected scope. Adapter
`scope_task_checks` supplies conditional keywords/checks; any task tagged `ui`,
`localization` or a performance topic must carry its checks regardless of layer,
and every presentation task must include `ui`.

Apply the common and adapter modularity rules from the base profile. For an
isolated boundary, tasks explicitly cover discovered manifest/project wiring,
minimal public API/visibility tests, module-level tests, consumer
integration/build, dependency graph and app-shell composition. A sealed
deviation keeps its typed seam and objective migration trigger in task context;
folder/layer creation never substitutes for physical isolation.
Plan accepts only the current modularity contract. A sealed legacy v0 package
cannot be expanded or re-planned and must route to a migration/new change.

Candidate meta is `planned`, `tasks_total` equals the derived file count,
`tasks_done: 0`, verification remains pending. Validate with `--mode plan
--change`. On failure return to `specified`, reset counts and report blockers.
Do not change contracts for planning convenience, write production code or
commit.
