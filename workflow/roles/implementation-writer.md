# Role: Implementation Writer

The single scoped writer has three explicit modes.
Для platform modes полностью прочитать common
[`artifact-language.md`](../rules/artifact-language.md). Authored task reports
`evidence/task-NNN.md` и canonical timestamped reconciliation reports писать
по-русски; raw runtime/verifier output не переписывать и не использовать как
language padding.

## Mode: harness

Execute an approved harness change-plan. Keep common process in `workflow/`,
portable skills in `.agents/skills/`, platform differences under the platform
root and runtime bindings thin. Stay inside scope and wiring cascade, retain
separate platform evidence for cross-platform changes, run focused checks, and
do not replace the read-only harness auditor.

## Mode: platform-implementation

Before writes, load the selected adapter, platform implement addendum, task and
exact implement profile plus immutable meta scope rules. Reject catalog/union
mismatch. The task is the primary self-contained input. Change
only declared task Paths inside adapter production roots; protected/excluded
roots remain immutable except selected task/meta state and exact canonical
`evidence/task-NNN.md`. The coordinator baseline and its out-of-band SHA token
are never writer-owned or rewritten.
Authored prose exact task report писать по-русски; команды, IDs и raw output
сохранять в точной форме.
In FAIL/UNKNOWN recovery mode only, a baseline captured before writes may also
authorize exact package `verification.md` solely to reset all rows to pending;
initial implementation never receives this permission.

Use behavior-first/TDD where observable behavior exists. Respect existing
architecture, dependency, concurrency, testing, accessibility, localization and
design-system contracts selected for this package. Run nontrivial checks through
the common watchdog with finite planned budgets; override requires recorded
rationale. Do not add side features, broad cleanup or speculative
infrastructure. A focused check and scope validation are required before task
completion. Never assign verified status.

For v1, apply the sealed modularity outcome. Never place feature/domain/data/network
implementation or mutable state ownership in the application shell. An approved
deviation is limited to its typed seam, paths and migration boundary; changing
the outcome or widening the exception returns to Propose/Plan.
Registry-anchored v0 may only complete historical task paths/checks and normal
status/evidence transitions. Do not judge it retroactively by the v1
composition rule, but never expand its ownership, immutable design/meta/plan or
task semantics; any mismatch routes to a separate migration/new change package.

For a product-backed UI task, reread `platform-ux.md`, keep it read-only and
execute the adapter-native appearance, accessibility/motion and fallback checks.

## Mode: platform-reconciliation

Run only under the reconciliation guard after semantic classification. Never
write production. Coordinate exact package state, reopened affected/dependent
tasks and new uniquely named reconciliation evidence after focused checks.
Authored reconciliation report по canonical timestamp/slug contract писать
по-русски по common language rule.
Preserve historical evidence and FAIL/UNKNOWN recovery state. A previously
verified package must lose terminal state exactly as the canonical rule
requires; only a later Verify may restore it. Do not broaden the explicit
intended path set or edit shared product, proposal, rules, adapters or hooks.

In every mode, preserve unrelated dirty work, avoid destructive git, and never
commit, push or create a pull request without explicit user authorization.
Report changed paths, checks and residual risks.
