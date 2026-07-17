---
name: archive
description: Collision-safe архивировать verified platform change, явно retired non-terminal platform package или явно retired shared product package. Использовать только по явному `$archive implementation ...` либо `$archive product ...`.
---

# Archive

Полностью выполнить [`workflow/phases/archive.md`](../../../workflow/phases/archive.md)
и [`archive-lifecycle.md`](../../../workflow/rules/archive-lifecycle.md).

- `$archive implementation <platform> <feature> [--change <change-id>]`
- `$archive implementation <platform> <feature> [--change <change-id>] --retire superseded|cancelled`
- `$archive product <feature>`

Для product archive использовать default request
`specs/product/_retirement-requests/<feature>/<YYYY-MM-DD-feature>.json` либо
явный `--request <safe-repo-relative-path>`. Request не хранить внутри active
product package; apply обязан сохранить validated copy как
`retirement-request.json` в product archive.

Всегда сначала dry-run `workflow/scripts/archive-change.py`, затем применять
только явный `--apply` после green gates. Не допускать overwrite/force,
traversal, ambiguous identity, stale evidence, active product references или
неполные platform dispositions. Implementation archive обязан сохранить
исходный verification fingerprint после relocation и создать проверяемый
`archive-receipt.json`; product disposition ссылается только на этот receipt.
Implementation apply также атомарно публикует полный verified contract в
feature-root `SPECIFICATION.md`; receipt v2 связывает published bytes с
immutable archived `implementation-spec.md`, не делая старые receipts зависимыми
от будущих замен current baseline.
Implementation retirement требует явный `--retire superseded|cancelled`,
принимает только валидный non-terminal `specified|planned|implementing`
package, создаёт `implementation-retirement` receipt и tombstone, но не
публикует и не меняет feature-root `SPECIFICATION.md`. Такой receipt разрешает
active ownership/tombstone classification, но не является delivery evidence для
`archive product completed`.
Implementation archive использует capability выбранного adapter и его
`archive_namespace`; platform addendum не дублирует общий move/rollback/receipt
algorithm. Product archive capability-independent и требует отдельного
retirement approval.
Для `completed` сохранить approved полный продуктовый контракт в долговечном
`specs/product/<feature>/SPECIFICATION.md`. Для `superseded`/`cancelled`
сохранить прежний baseline без продвижения retired candidate. Baseline является
read-only knowledge input будущих lifecycle, не active package и не tombstone.

Manual-only. Не коммитить.
