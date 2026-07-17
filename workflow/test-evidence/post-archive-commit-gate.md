# Post-archive commit gate evidence

## Change plan

- **Тип:** rule + phase + script + skill
- **Операция:** modify
- **Зачем:** commit gate жёстко зависел от момента lifecycle: до archive
  production paths покрывались active task trail, а после archive active
  `meta.json` исчезал и `reconcile-implementation`/`pre-commit-check` блокировали
  тот же verified delivery set. Нужно разрешить commit как до, так и после
  завершения lifecycle, не ослабляя exact intended path binding.
- **Scope:** common

## Locate

- **Затронутый flow:** `process/flows.md` → explicit commit flow; platform
  lifecycle → `reconcile-implementation` → `pre-commit-check`.
- **Канонический владелец:** `workflow/rules/pre-commit-integrity.md`,
  `workflow/rules/implementation-reconciliation.md`,
  `workflow/phases/pre-commit-check.md`,
  `workflow/phases/reconcile-implementation.md`.
- **Placement:** canonical common scripts/rules/phases; portable skills updated
  as runtime entries.
- **SSOT-проверка:** active task trail already lived in `pre-commit-check.py`;
  archive receipt validation already lived in `archive-change.py`. This change
  adds archived task trail lookup to the same pre-commit owner and read-only
  tombstone/receipt routing to the same reconciliation owner.
- **Просмотрено:** `.agents/skills/harness-change/SKILL.md`,
  `workflow/phases/harness-change.md`,
  `workflow/rules/pre-commit-integrity.md`,
  `workflow/phases/pre-commit-check.md`,
  `.agents/skills/pre-commit-check/SKILL.md`,
  `.agents/skills/reconcile-implementation/SKILL.md`,
  `workflow/phases/reconcile-implementation.md`,
  `workflow/rules/implementation-reconciliation.md`,
  `workflow/scripts/pre-commit-check.py`,
  `workflow/scripts/reconcile-implementation.py`, `process/flows.md`,
  `workflow.md`.

## Behavior

- Before archive: production path coverage remains `completed active task +
  staged evidence`.
- After archive: production path coverage may come from `completed archived
  task + verified implementation archive receipt`.
- `implementation-retirement` receipts remain non-delivery evidence and do not
  satisfy production coverage.
- Post-archive reconciliation is read-only `ALIGNED`; `start` reports
  `guard_state: not-required-post-archive-immutable`.
- Exact intended/staged equality and adapter production ownership remain
  unchanged.

## Root documentation impact

- **README.md:** no-impact — top-level repository capability does not change.
- **workflow.md:** update — operational commit guide now names active task trail
  or archived receipt trail.
- **deep-info.md:** update/generated — inventory includes this evidence and
  generated skill/phase projections.

## Evidence

```text
rtk python3 -m py_compile workflow/scripts/pre-commit-check.py workflow/scripts/reconcile-implementation.py

rtk python3 workflow/scripts/pre-commit-check.py --self-test
pre-commit-check self-test: PASS (exact one-shot receipt, index-only, evidence/tools, adapter fail-closed, rename/copy/delete)

rtk python3 workflow/scripts/reconcile-implementation.py --self-test
reconcile-implementation self-test: PASS (drift, routes, guard, recovery, platforms, copy/rename/delete)

rtk python3 workflow/scripts/harness-docs.py check --json
{"status":"PASS", ...}

rtk python3 workflow/scripts/harness-lint.py --json
{"grade":"A","critical":0,"warnings":0,"findings":[]}
```

Real post-archive pressure checks:

```text
rtk python3 workflow/scripts/reconcile-implementation.py inspect --platform android --feature user-profile-auth --change user-profile-auth --path Android/auth/src/main/java/ru/home/sysdevsc/auth/data/DefaultAuthApiService.kt --json
outcome: ALIGNED
package_state: archived
task_coverage: task-004

rtk python3 workflow/scripts/reconcile-implementation.py inspect --platform ios --feature user-profile-auth --change user-profile-auth-public-contract-repair --path iOS/AuthFeature/Sources/AuthFeature/AuthFeatureFactory.swift --json
outcome: ALIGNED
package_state: archived
task_coverage: task-001, task-002
```

## Residual risk

Archived receipt trail proves lifecycle coverage, not new drift repair. Any new
post-archive behavior or uncovered production path still requires a new active
change package. In the current Android worktree this correctly still flags
`Android/app/src/main/res/values/strings.xml` as uncovered by the archived
receipt; that is a package coverage issue, not a commit-timing dependency.
