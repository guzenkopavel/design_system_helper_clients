# Implementation reconciliation

Implementation reconciliation is the pre-delivery boundary between an explicit
user-owned production change set and one platform package. It runs before
staging. The coordinator may invoke it after explicit commit intent, but it
must receive the intended set explicitly; it never treats every dirty path as
authorized scope. Every platform package identity (`platform + feature +
change_id`) gets an independent invocation, guard and report. Therefore both a
cross-platform change and two packages on the same platform are split.

Form:

```text
reconcile-implementation <platform> <feature> [--change <change-id>] \
  --path <repo-relative-path> [--path <repo-relative-path> ...]
```

Every path must be repo-relative, belong to the selected adapter production
roots and be present in the current Git change set. Deletion is named by its
old path. Rename requires both old and new paths; neither side may be inferred.
A pre-stage copy is an explicit new changed path; its read-only source need not
be authorized. If staged Git later classifies it as a copy, the read-only gate
checks both candidates and task trails. Unknown platform/package, ambiguity,
archived package, unsafe/outside-ownership path or a mixed ownership set routes
without writes. An adapter-owned uncovered path is valid drift: repair or add
its task and focused evidence inside the guard.

## Classification and routing

- `aligned`: current tasks and platform contracts already describe the intended
  code; only status/evidence reconciliation is needed.
- `task-drift`: platform contracts/design remain true, but task decomposition,
  paths, dependencies or focused checks must be repaired.
- `platform-implementation-drift`: observable shared behavior remains unchanged,
  but platform requirements, design, verification mapping and dependent tasks
  need coherent repair.
- shared behavior `PRESENT` or product impact `UNCERTAIN`: `ROUTE_REQUIRED` to
  Discovery/Elaborate. Reconciliation must not edit the shared product package.

Classification is semantic work by the canonical roles, not a filename
heuristic. Ambiguity and archive routing produce zero repository writes.

## Entry state

| Baseline | Result |
|---|---|
| `draft` | `ROUTE_REQUIRED` to Propose; zero writes |
| `specified` | `ROUTE_REQUIRED` to Plan; zero writes |
| `planned` | reconciliation may start; success must end `implementing` |
| `implementing` + verification `pending` | reconciliation may start and must remain `implementing` |
| `verified` | reconciliation may start and invalidate terminal state |
| verification `FAIL` or `UNKNOWN` | `ROUTE_REQUIRED` to canonical `$implement` recovery; zero writes |
| `archived` | immutable; zero writes |

## Write and preservation boundary

The explicit production paths are read-only reconciliation input. The guarded
write allowlist is limited to the selected active platform package:

- `implementation-spec.md`, `design.md`, `verification.md`, `meta.json`;
- `plan/README.md`, `plan/rule-selection.json`, `plan/task-NNN.md`;
- a new uniquely named `evidence/reconciliation-*.md` file.

No other write is authorized. In particular reconciliation never changes
production, the Git index, shared product artifacts, `proposal.md`, adapter or
workflow authorities, historical evidence, hooks, archive, another package or
unrelated dirty state. Existing evidence files are immutable.

For `aligned`, contract and task semantics remain unchanged. `task-drift` may
change task semantics and coherent plan state but not upstream platform
contracts or sealed engineering-scope authority. `platform-implementation-drift`
may repair platform implementation spec, design, verification mapping and the
affected task graph, while shared product contracts and proposal remain fixed.
Task-file add/change/delete is limited to the union of baseline and final direct
owners of the explicit paths plus their transitive dependent closures. Every
unrelated task is full-content immutable, including `Status` and `Evidence`,
even though it lives in the selected plan. Separate semantic hashes still prove
that task/platform drift actually repaired task semantics.

Meta changes are field-level guarded. Every class may change only lifecycle
status/counters and verification invalidation fields. Platform implementation
drift may additionally repair `engineering_scopes`, `applicable_rule_files`,
`design_gate` and `rule_selection_snapshot` coherently with Plan. Identity,
intake/change type, tier, product status/impact/approval and
`shared_product_spec` are immutable for every class.

## State, evidence and validation

Reopen every affected task and its complete transitive dependent closure before
claiming reconciliation. A task becomes done again only after a fresh focused
check and a new reconciliation evidence file records exact intended paths,
command and result. Every affected/dependent task evidence names the complete
triggering intended path set, even when that task only depends on its direct
owner. It contains one exact structural list field `- Result: PASS`; missing,
duplicate, indented, whitespace/case/decorated, `FAIL` or `UNKNOWN` Result-like
fields invalidate the run. Narrative that does not define a Result field remains
allowed.
Historical evidence is preserved.

If the package was `verified`, invalidate terminal state before repair:
`status: implementing`, all verification rows `pending`, empty `problems`,
`verification_status: pending`, and null `verified_at`/`verification_state`.
Delete no historical evidence. Existing `FAIL`/`UNKNOWN`, problem IDs and
recovery state route to canonical `$implement` recovery before the guard; the
post-guard defense still rejects any attempted clearing.

Run the final platform validator in `implement` mode. A previously verified
package requires fresh `$verify` to restore terminal state. A non-terminal
package may proceed to scoped staging/pre-commit after `RECONCILED`; Verify
remains the later terminal lifecycle step rather than a new universal commit
gate.

## Guard protocol

Use `workflow/scripts/reconcile-implementation.py`:

1. `inspect` validates identity, intended paths, coverage and routing without
   writes. `DRIFT` is an expected non-failure result; `ROUTE_REQUIRED` blocks.
2. `start` requires the explicit semantic classification and captures a private
   mode `0600` baseline outside the repository, including exact HEAD commit and
   symbolic/detached identity.
3. Roles make only allowed package repairs and focused checks.
4. `check <token>` proves production, index, shared/proposal/rules/history and
   unrelated state were preserved, HEAD did not move, required state/evidence
   semantics hold, and the final validator is green. A commit or branch/detached
   HEAD move between `start` and `check` is invalid.

Report classification, package, intended paths, affected tasks, checks and
final state before staging. The delivery sequence is exactly:

```text
explicit commit intent
→ explicit intended path set
→ reconcile-implementation per platform package identity
→ reconciliation report
→ staging of the approved set
→ pre-commit-check
→ commit
```

The staged gate and runtime/Git hooks remain read-only. They may emit an
actionable hint to run reconciliation for uncovered production paths, but must
never invoke it, repair files or infer authorization.
