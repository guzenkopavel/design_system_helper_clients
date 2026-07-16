---
name: pre-commit-check
description: Проверить staged index перед явным commit intent. Использовать при `$pre-commit-check` и всегда перед выполнением просьбы commit/закомить; gate сам не stage/commit/push.
---

# Pre-commit Check

Полностью выполнить [`workflow/phases/pre-commit-check.md`](../../../workflow/phases/pre-commit-check.md)
и [`pre-commit-integrity.md`](../../../workflow/rules/pre-commit-integrity.md).

После explicit commit intent сначала зафиксировать явный intended path set и до
staging выполнить отдельный `$reconcile-implementation` для каждой
platform/feature/change identity. Cross-platform и несколько packages одной
платформы делятся на независимые запуски; весь dirty worktree не
подставлять. После reconciliation report проверить ownership/status, stage
только уже разрешённый set и запустить canonical
`pre-commit-check.py --staged --path <path>...` с exact intended set;
не подменять staged evidence worktree-проверкой или старым receipt. Exact PASS
создаёт short-lived private receipt для текущего staged fingerprint. Применить
platform addendum для затронутых production paths.

Требовать exact staged/intended equality: rename old/new mutable; copy source
read-only unchanged и destination mutable, обе стороны входят в receipt. Unique
active package owner проверять только для mutable production paths. Extra/missing/unsafe path
блокирует gate; unrelated unstaged state допустим. Runtime preview не потребляет
receipt, tracked `--hook` потребляет его one-shot; generic hook без свежего
receipt не заменяет и не обходит coordinator intended binding.

Gate не расширяет delivery authorization и не делает `git add`, commit, push,
hook installation или destructive recovery. Если пользователь уже явно
попросил commit, после свежего GREEN coordinator продолжает тот же commit без
повторного запроса разрешения.
Gate может только подсказать reconciliation для uncovered path; он не запускает
skill и не исправляет package.
