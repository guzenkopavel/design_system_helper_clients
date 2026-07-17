---
name: reconcile-implementation
description: Сверить явный набор platform production changes с active implementation package или verified archived implementation receipt до staging и безопасно восстановить/подтвердить package evidence/state.
---

# Reconcile Implementation

Полностью выполнить
[`workflow/phases/reconcile-implementation.md`](../../../workflow/phases/reconcile-implementation.md)
и
[`implementation-reconciliation.md`](../../../workflow/rules/implementation-reconciliation.md).

Форма: `$reconcile-implementation <platform> <feature> [--change <change-id>]
--path <repo-relative>...`. Intended paths задаются явно; не подставлять весь
dirty worktree. Cross-platform change — два независимых запуска.
Каждый отдельный feature/change package, даже на одной платформе, также требует
собственный запуск, guard и report.

Сначала read-only `reconcile-implementation.py inspect`, затем semantic
classification canonical roles. Shared behavior `PRESENT`/`UNCERTAIN`,
ambiguity, unsafe/outside/mixed ownership paths маршрутизируются с нулём
записей; symlink file/directory/proposed-child блокируется canonical ownership
helper. Adapter-owned uncovered active path — это drift: добавить/исправить
task, plan state и fresh evidence. Post-archive path допустим только как
read-only `ALIGNED`, если tombstone указывает на verified implementation archive
receipt; archived tasks или verified scope preferred, но валидный receipt может
покрывать coherent package-level delivery slice с warnings.
retirement/non-PASS archive не является delivery coverage. `draft` идёт в
Propose, `specified` в Plan, а `FAIL`/`UNKNOWN` в canonical `$implement`
recovery до guard. Copy identity возникает только при явном source+destination
или Git-reported copy; совпавший blob обычного added file source peer не
требует. Для поддержанного active класса запустить guard `start`,
менять только разрешённые package artifacts, выполнить focused checks и
завершить `check`; для verified archived package guard не нужен и report
остаётся read-only.
Guard scoped выбранной identity и не блокируется disjoint platform/feature/
product dirty, index или commit; selected package/intended paths/shared spec/
rules/adapter/control plane остаются неизменяемыми вне allowlist. Ambiguous
cross-package production owner блокирует `inspect` до записей.

Не менять production/index/shared product/proposal/rules/hooks/history и не
stage/commit/push. Перед staging выдать полный reconciliation report.
