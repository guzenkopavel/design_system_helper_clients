---
name: archive
description: Collision-safe архивировать verified platform change или явно retired shared product package. Использовать только по явному `$archive implementation ...` либо `$archive product ...`.
---

# Archive

Полностью выполнить [`workflow/phases/archive.md`](../../../workflow/phases/archive.md)
и [`archive-lifecycle.md`](../../../workflow/rules/archive-lifecycle.md).

- `$archive implementation <platform> <feature> [--change <change-id>]`
- `$archive product <feature>`

Всегда сначала dry-run `workflow/scripts/archive-change.py`, затем применять
только явный `--apply` после green gates. Не допускать overwrite/force,
traversal, ambiguous identity, stale evidence, active product references или
неполные platform dispositions. Implementation archive обязан сохранить
исходный verification fingerprint после relocation и создать проверяемый
`archive-receipt.json`; product disposition ссылается только на этот receipt.
Implementation archive использует capability выбранного adapter и его
`archive_namespace`; platform addendum не дублирует общий move/rollback/receipt
algorithm. Product archive capability-independent и требует отдельного
retirement approval.

Manual-only. Не коммитить.
