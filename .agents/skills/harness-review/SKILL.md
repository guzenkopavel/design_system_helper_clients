---
name: harness-review
description: Проверять сам workflow-харнес репозитория на структурную и смысловую согласованность. Использовать по явному вызову harness-review, после harness-change или для периодического аудита правил, фаз, skills, ролей, hooks и process map; совмещать детерминированный lint, read-only аудит и отдельные iOS/Android evidence для cross-platform scope.
---

# Harness Review

Канонический процесс: [`workflow/phases/harness-review.md`](../../../workflow/phases/harness-review.md).

1. Запустить `python3 workflow/scripts/harness-docs.py check --json`, затем
   `python3 workflow/scripts/harness-lint.py --json`.
2. Передать scope, docs/lint output роли `harness-auditor` для проверки SSOT,
   логики, canonical↔adapter parity, prose references, roster и placement.
3. Проверить semantic freshness трёх audience layers: capabilities, invocation,
   ownership, write/evidence claims и отдельные iOS/Android утверждения.
4. Любой stale generated block, missing inventory/binding или неверный manual
   claim блокирует `CLEAN`.
5. Свести findings в один graded fix-list, передать исправления только
   `implementation-writer` и повторить проверки.
6. Завершить при docs PASS + grade A + `CLEAN`; для `cross-platform` подтвердить
   iOS и Android.

Выбрать нативный auditor binding по
[`runtime-adapters`](../../../workflow/rules/runtime-adapters.md).

Аудитор работает read-only. Не создавать коммит без явной просьбы.
