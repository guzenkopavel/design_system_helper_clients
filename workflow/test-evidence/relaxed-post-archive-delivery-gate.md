# Relaxed post-archive delivery gate

## Change plan

- **Тип:** rule + script + skill doc.
- **Операция:** modify.
- **Зачем:** post-archive commit gate блокировал цельные рабочие срезы, если
  финальный production set шире exact archived task path list или если archive
  file совпадал blob'ом с другим tracked файлом. Это вынуждало либо резать
  production commit на нерабочие части, либо искусственно переписывать archive
  evidence после terminal verification.
- **Scope:** common. Симптом проявился на iOS, но владелец — общий
  `pre-commit`/`reconcile-implementation`/`git_change_paths` contract.

## Locate

- **Затронутый flow:** `process/flows.md#explicit-commit-flow`.
- **Канонический владелец:** `workflow/rules/pre-commit-integrity.md` и
  `workflow/rules/implementation-reconciliation.md`.
- **Placement:** canonical common + portable skills.
- **SSOT-проверка:** существующие владельцы найдены по `pre-commit gate`,
  `implementation reconciliation`, `copy source`, `verified archive receipt`.

## Decision

1. Ordinary added files are not inferred as copy identities only because their
   blob matches some HEAD file. Explicit copy remains strict: source must be
   named, unchanged, safe and read-only.
2. Active-package delivery remains path/task/evidence driven.
3. Post-archive delivery may use a valid current verified implementation
   archive receipt as package-level terminal proof. Exact archived task or
   verified-scope coverage remains preferred and is reported when available;
   missing path-level coverage becomes a warning, not a blocker.
4. Project/tool evidence for post-archive verified receipt trails is satisfied
   by terminal archive evidence; active tasks still need staged command/result
   evidence.
5. Implementation-retirement receipts still do not satisfy delivery coverage.
6. Exact staged/intended equality, unsafe path checks, ownership checks,
   generated/local/secret checks, receipt TTL and hooks remain intact.

## Root documentation impact

- **README.md:** no-impact — high-level repository entry does not describe
  commit gate internals.
- **workflow.md:** update — explicit commit flow now mentions package-level
  post-archive coverage and non-automatic copy inference.
- **deep-info.md:** update — detailed lifecycle notes now mention relaxed
  post-archive package receipt coverage.

## Evidence checklist

- `rtk python3 workflow/scripts/git_change_paths.py --self-test` — PASS.
- `rtk python3 workflow/scripts/pre-commit-check.py --self-test` — PASS.
- `rtk python3 workflow/scripts/reconcile-implementation.py --self-test` —
  PASS.
- Focused iOS evidence: full staged iOS `user-profile-auth` slice
  (`iOS/AuthFeature`, `iOS/SysDevScen`, `iOS/specs/user-profile-auth`) —
  `reconcile-implementation.py inspect --platform ios --feature
  user-profile-auth --change user-profile-auth-public-contract-repair` returned
  `ALIGNED`, `coverage_mode: verified-archive-package`; then
  `pre-commit-check.py --staged --path ...` returned `PASS`.
- `rtk python3 workflow/scripts/harness-docs.py render` — PASS; regenerated
  `deep-info.md` inventory after excluding runtime worktrees.
- `rtk python3 workflow/scripts/harness-docs.py check --json` — PASS.
- `rtk python3 workflow/scripts/harness-security-audit.py --json` — PASS.
- `rtk python3 workflow/scripts/harness-lint.py --json` — grade A, zero
  warnings.
- Android evidence: `pre-commit-check.py --self-test` exercises Android adapter
  fixtures; runtime worktree exclusions are common scanner behavior.
