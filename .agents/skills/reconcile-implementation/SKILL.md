---
name: reconcile-implementation
description: Сверить явный набор platform production changes с active implementation package до staging и безопасно восстановить package evidence/state.
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
classification canonical roles. Shared behavior `PRESENT`/`UNCERTAIN`, archive,
ambiguity, unsafe/outside/mixed ownership paths маршрутизируются с нулём
записей. Adapter-owned uncovered path — это drift: добавить/исправить task,
plan state и fresh evidence. `draft` идёт в Propose, `specified` в Plan, а
`FAIL`/`UNKNOWN` в canonical `$implement` recovery до guard. Для
поддержанного класса запустить guard `start`, менять только разрешённые package
artifacts, выполнить focused checks и завершить `check`.

Не менять production/index/shared product/proposal/rules/hooks/history и не
stage/commit/push. Перед staging выдать полный reconciliation report.
