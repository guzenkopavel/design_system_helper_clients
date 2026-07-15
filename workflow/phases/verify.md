---
phase: verify
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/verification.md
  - <platform>/specs/<feature>/changes/<change-id>/evidence/
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
requires_verification: terminal
recommended_roles:
  - verifier
---

# Phase: Verify

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
rule change and overwrite of pre-existing evidence while preserving unrelated
dirty/index state that existed before the baseline. Only after this guard is green may
the coordinator persist recovery task reopening or terminal state capture.

The read-only-for-production `verifier` rereads current shared/platform
contracts, task files, realized code and applicable platform rules. It reruns
each declared method and writes only scoped evidence under package `evidence/`.
Every verification row receives exact `PASS`, `FAIL` or `UNKNOWN`; concrete
evidence paths are mandatory.

Resolve `--phase verify` with the unchanged meta scopes and reject any mismatch
with the stored applicable lifecycle union. Independently derive methods from
the verification matrix and selected scope risks. Nontrivial commands use the
watchdog with discovered plan budgets. Runtime, UI, accessibility, localization,
concurrency and performance evidence is required only when selected/applicable;
unavailable required infrastructure yields `UNKNOWN`, never an invented PASS.

If any row is non-PASS, persist a recovery state: keep `status: implementing`,
set `verification_status: FAIL` when at least one row is FAIL and otherwise
`UNKNOWN`, keep `verified_at`/`verification_state` null, and set `problems` to
the exact non-PASS contract IDs. First reopen every done task whose Inline
contract context cites one of those IDs, then reopen the complete transitive
dependent closure of each such task. Every reopened task becomes
`Status: pending`, `Evidence: none`; downstream tasks need not cite the failed
contract. Re-derive `tasks_done`. If no task directly maps a failing contract,
block and require plan repair; never invent implementation scope.

After every row is PASS, clear `problems`, capture current state with
`capture-verification-state.py --write`, set candidate `status: verified`,
`verification_status: PASS`, `verified_at` and `verification_state`, then run
the terminal validator in `verify` mode. If validation fails, retain `implementing` and
record the failure; writer narrative or prior evidence cannot substitute for a
fresh run. No production writes or commit.
