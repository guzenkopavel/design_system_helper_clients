# Implementation reconciliation evidence

## Scope and documentation impact

- scope: `cross-platform`, with independent iOS and Android addenda/evidence;
- `README.md`: `no-impact` for manual product-facing prose; the generated
  capability projection is refreshed mechanically because the platform addendum
  inventory changed;
- `workflow.md`: `update` — adds the pre-staging skill and commit sequence;
- `deep-info.md`: `update` — adds guard/write-boundary semantics; generated
  wiring, runtime parity and inventory are refreshed.

## RED baseline

Before implementation there was no portable `reconcile-implementation` skill,
canonical owner, explicit-path guard or pre-staging package repair. Uncovered
production paths were rejected by gate/hook without a canonical route. Existing
Plan immutability provided no bounded exception for implementation drift.

## GREEN contract

- explicit `<platform> <feature> [--change] --path ...`; no dirty-tree
  inference, both rename sides required, every platform package identity gets a
  separate call/guard/report;
- semantic `aligned`, `task-drift`, `platform-implementation-drift` classes;
  shared behavior present/uncertain routes to Discovery/Elaborate with zero
  writes;
- stdlib `inspect/start/check` guard with private mode `0600` state;
- production, index, shared product, proposal, rules/adapters/hooks, archive,
  historical evidence and unrelated state remain immutable;
- affected tasks and transitive dependents reopen, focused checks create only
  new unique reconciliation evidence linked to the complete triggering path
  set; verified state is invalidated, and FAIL/UNKNOWN routes to canonical
  Implement recovery before writes;
- per-class meta allowlists preserve identity/intake/product/approval/tier and
  shared product authority;
- final platform validator runs in implement mode; fresh Verify restores a
  previously invalidated terminal claim, while a non-terminal package may
  proceed to scoped staging/pre-commit;
- staged gate and runtime hooks remain read-only and expose only an actionable
  reconciliation hint.
- guard binds to HEAD commit/ref identity; task semantics are writable only in
  baseline/current direct + dependent closure; unrelated task files are fully
  immutable; evidence accepts one exact `- Result: PASS` field.

## Pressure evidence

| Scenario | Result |
|---|---|
| clean aligned iOS/Android path | `RECONCILED`, index and unrelated state preserved |
| adapter-owned uncovered path | new coherent task/plan/evidence → `RECONCILED` |
| uncovered path, then fixture-only scoped stage of production + package artifacts | canonical pre-commit `PASS` |
| task drift / platform implementation drift | bounded package repair + implement validator |
| shared behavior or uncertain impact | `ROUTE_REQUIRED`, zero writes |
| unsafe/outside/mixed ownership path, archive, ambiguous package | blocked before guard writes |
| one-sided rename | route required; both explicit sides accepted |
| pre-stage copy | explicit new path; read-only source need not be authorized |
| deletion | accepted by explicit old path |
| `draft` / `specified` | route to Propose / Plan with zero writes |
| `planned` success | final state must be `implementing` |
| production/index/shared/proposal/rule/history/unrelated mutation | `INVALID` |
| product approval/shared spec/change type meta mutation | `INVALID` |
| prior verified package | terminal fields/rows reset, historical evidence preserved |
| prior FAIL/UNKNOWN | route to canonical `$implement` recovery, zero writes; bypass defense rejects clearing |
| dependent evidence missing triggering paths, focused result or unique file | `INVALID` |
| exact PASS plus indented FAIL, duplicate, spacing/case/decorated variant, `FAIL` or `UNKNOWN` | `INVALID` |
| narrative that does not define a Result field | remains valid |
| empty commit or other HEAD/ref move after guard start | `INVALID` |
| implementing → planned | `INVALID`; implementing must remain implementing |
| unrelated task Status/Evidence change with coherent counters/plan bookkeeping | `INVALID` outside affected/dependent closure |
| malicious gate/hook auto-invocation wiring | harness lint critical finding |

## Commands

```text
python3 workflow/scripts/reconcile-implementation.py --self-test
reconcile-implementation self-test: PASS (drift, routes, guard, recovery, platforms, copy/rename/delete)

python3 workflow/scripts/pre-commit-check.py --self-test
pre-commit-check self-test: PASS (index-only, evidence/tools, adapter fail-closed, rename/copy/delete)

python3 workflow/hooks/hook-runner.py --self-test
hook-runner self-test: PASS (git guards, platform edit guards, post-edit warnings)

python3 workflow/scripts/harness-lint.py --self-test
harness-lint self-test: PASS (profiles + hooks + deep review security mutations)
harness-docs self-test: PASS (markers, freshness, parity, isolation)

python3 workflow/scripts/harness-lint.py --warn-as-error
Harness lint: grade A (0 critical, 0 warnings)

python3 workflow/scripts/harness-docs.py check
Harness docs: PASS
```

All remaining canonical script self-tests pass: context retrieval, platform
validator, implementation scope, verification-state capture, dual archive,
watchdog, deep-review validator/reader/guard/security and explicit hook setup.
Both active `client-bootstrap/initial-scaffold` packages validate in implement
mode independently. `git diff --check`, Python compileall and forbidden
reference/absolute-path scan are clean.
