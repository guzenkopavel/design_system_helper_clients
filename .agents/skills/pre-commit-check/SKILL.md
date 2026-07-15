---
name: pre-commit-check
description: Проверить staged index перед явным commit intent. Использовать при `$pre-commit-check` и всегда перед выполнением просьбы commit/закомить; gate сам не stage/commit/push.
---

# Pre-commit Check

Полностью выполнить [`workflow/phases/pre-commit-check.md`](../../../workflow/phases/pre-commit-check.md)
и [`pre-commit-integrity.md`](../../../workflow/rules/pre-commit-integrity.md).

Сначала проверить ownership/status до staging. Затем запустить canonical
`pre-commit-check.py --staged`; не подменять staged evidence worktree-проверкой
или старым receipt. Применить platform addendum для затронутых production paths.

Gate не расширяет delivery authorization и не делает `git add`, commit, push,
hook installation или destructive recovery. Если пользователь уже явно
попросил commit, после свежего GREEN coordinator продолжает тот же commit без
повторного запроса разрешения.
