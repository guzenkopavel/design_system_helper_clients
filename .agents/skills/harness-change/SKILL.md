---
name: harness-change
description: Изменять сам workflow-харнес репозитория — правила, фазы, skills, команды, роли, hooks, скрипты, шаблоны и process map. Использовать по явному вызову harness-change или когда нужно добавить, изменить, переместить либо удалить harness-механику с проверкой common/iOS/Android scope, wiring cascade и финальным harness-review.
---

# Harness Change

Канонический процесс: [`workflow/phases/harness-change.md`](../../../workflow/phases/harness-change.md).

1. Заполнить [`change-plan`](../../../workflow/templates/harness-change.md) и
   определить `common`, `ios`, `android` или `cross-platform` scope.
2. Найти канонического владельца через
   [`process/`](../../../process/README.md); проверить назначение и синонимы,
   чтобы не создать дубль.
3. Передать scoped plan роли `implementation-writer` как единственному writer.
4. Для нового hard rule, skill или роли применить
   [`writing-skills`](../writing-skills/SKILL.md).
5. Синхронизировать process map, roster, skill metadata, индексы и entry points.
6. Для `README.md`, `workflow.md` и `deep-info.md` записать отдельный
   `update|no-impact` disposition с rationale по
   [`repository-documentation`](../../../workflow/rules/repository-documentation.md).
7. В конце wiring cascade выполнить `harness-docs.py render`, затем read-only
   `harness-docs.py check --json`; generated blocks вручную не править.
8. Применить [`harness-review`](../harness-review/SKILL.md) до grade A + `CLEAN`.
9. Для `cross-platform` потребовать отдельные iOS и Android evidence.
10. Сообщить изменённые каноны, адаптеры, wiring, проверки и остаточные риски.

Выбрать нативные invocation и role bindings по
[`runtime-adapters`](../../../workflow/rules/runtime-adapters.md).

Не применять для продуктового кода. Не создавать коммит без явной просьбы.
