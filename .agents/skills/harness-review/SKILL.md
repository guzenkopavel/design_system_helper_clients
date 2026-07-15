---
name: harness-review
description: Проверять сам workflow-харнес репозитория на структурную и смысловую согласованность. Использовать по явному вызову harness-review, после harness-change или для периодического аудита правил, фаз, skills, ролей, hooks и process map; совмещать детерминированный lint, read-only аудит и отдельные iOS/Android evidence для cross-platform scope.
---

# Harness Review

Канонический процесс: [`workflow/phases/harness-review.md`](../../../workflow/phases/harness-review.md).

1. Запустить `python3 workflow/scripts/harness-lint.py` или `--json`.
2. Передать scope и lint output роли `harness-auditor` для проверки SSOT,
   логики, canonical↔adapter parity, prose references, roster и placement.
3. Свести findings в один graded fix-list.
4. Передать исправления только `implementation-writer` и повторить проверки.
5. Завершить при grade A + `CLEAN`; для `cross-platform` отдельно подтвердить
   iOS и Android.

Выбрать нативный auditor binding по
[`runtime-adapters`](../../../workflow/rules/runtime-adapters.md).

Аудитор работает read-only. Не создавать коммит без явной просьбы.
