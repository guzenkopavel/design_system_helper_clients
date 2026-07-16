---
phase: verify
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/verification.md
  - <platform>/specs/<feature>/changes/<change-id>/evidence/
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
  - <platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md (recovery only)
requires_verification: terminal
recommended_roles:
  - verifier
---

# Phase: Verify

Require adapter `verify` capability before package discovery or baseline writes.

Form: `verify <platform> <feature> [--change <change-id>]`. Resolve identity and
adapter before writes. Require all tasks done with focused evidence and no
blockers/problems.

Before dispatching `verifier`, capture
`evidence/verify-scope-baseline.json` with
`validate-implementation-scope.py verify-snapshot`. Coordinator retains the
emitted SHA-256 token outside repository state and passes it to `verify-check`
as `--expected-sha256`; baseline rewriting is therefore a failure. Immediately
after verifier writes rows/new evidence and permitted verification meta fields,
run `verify-check`. It rejects every production, task, plan, contract, adapter or
rule change and overwrite of pre-existing evidence in the selected verify lane.
Lane включает package, union realized task Paths, Read-only context, shared
spec, applicable rules, adapter и common/platform control plane; disjoint
platform/feature/product dirty, index и commits не инвалидируют baseline. Only after this guard is green may
the coordinator persist recovery task reopening or terminal state capture.

The read-only-for-production `verifier` rereads current shared/platform
contracts, task files, realized code and applicable platform rules. It reruns
each declared method and writes only scoped evidence under package `evidence/`.
Every verification row receives exact `PASS`, `FAIL` or `UNKNOWN`; concrete
evidence paths are mandatory.
Каждая атомарная AC/verification dimension обязана иметь ровно одну собственную
row и concrete evidence observation. Terminal `PASS` разрешён только при exact
coverage всех atomic obligations; PASS соседней строки или prose summary не
закрывают отсутствующую dimension.
Authored prose в `verification.md` и собственных reports писать по-русски по
[`artifact-language`](../rules/artifact-language.md); exact statuses, IDs,
paths, commands и API names сохранять без перевода.

Resolve `--phase verify` with the unchanged meta scopes and reject any mismatch
with the stored applicable lifecycle union. Independently derive methods from
the verification matrix and selected scope risks. Nontrivial commands use the
watchdog with discovered plan budgets. Runtime, UI, accessibility, localization,
concurrency and performance evidence is required only when selected/applicable;
unavailable required infrastructure yields `UNKNOWN`, never an invented PASS.
Ненаблюдённая runtime/appearance/accessibility dimension всегда `UNKNOWN`, даже
если связанный happy path имеет `PASS`.
Для current v1 product-backed `ui` verifier заполняет exact common `NATIVE-*` set из
verification template structured observation records. Missing/duplicate ID,
row/record mismatch или PASS без underlying evidence блокируют terminal state.
For product-backed UI, reread `platform-ux.md` and collect reproducible native
appearance evidence for its scenarios, light/dark/contrast, motion/accessibility
and availability fallback. This harness gate does not claim actual rendering.

For `modularity_contract_version: 1`, apply the common and adapter modularity
rules from the verify base. Inspect the realized physical dependency graph,
public API/visibility, module-level tests, consumer integration/build and
application-shell allowlist. A folder/layer is not isolation; unavailable
graph/build tooling produces `UNKNOWN`. Registry-anchored v0 instead verifies
only its resolver-selected historical projection and adapter
`legacy_task_checks`; it receives no retroactive v1 Modularity decision or
app-shell checks and cannot expand ownership or immutable package structure.
Он также не получает новые v1 authored-meta language или `NATIVE-*` obligations.

If any row is non-PASS, persist a recovery state: keep `status: implementing`,
set `verification_status: FAIL` when at least one row is FAIL and otherwise
`UNKNOWN`, keep `verified_at`/`verification_state` null, and set `problems` to
the exact non-PASS contract IDs. First reopen every done task whose Inline
contract context cites one of those IDs, then reopen the complete transitive
dependent closure of each such task. Every reopened task becomes
`Status: pending`, `Evidence: none`; downstream tasks need not cite the failed
contract. Re-derive `tasks_done`. If no task directly maps a failing contract,
block and require plan repair; never invent implementation scope.
Native non-PASS obligations маппятся не на fake contract IDs, а на все tasks с
sealed `ui` scope и их dependent closure; отсутствие такой task требует plan
repair.

After every row is PASS, clear `problems`, capture current state with
`capture-verification-state.py --write`, set candidate `status: verified`,
`verification_status: PASS`, `verified_at` and `verification_state`, then run
the terminal validator in `verify` mode. If validation fails, retain `implementing` and
record the failure; writer narrative or prior evidence cannot substitute for a
fresh run. No production writes or commit.

State capture always includes the common verification evidence rule, this phase
and the selected platform verify addendum as mandatory terminal contracts. They
are fingerprinted outside the sealed engineering rule union, deduplicated when
already selected, and their absence blocks capture.

Any successful reconciliation invalidates prior terminal evidence for affected
implementation. Run this phase fresh after reconciliation; its package report
or implement-mode validator is not terminal verification.
