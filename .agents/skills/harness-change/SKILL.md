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
6. Применить [`harness-review`](../harness-review/SKILL.md) до grade A + `CLEAN`.
7. Для `cross-platform` потребовать отдельные iOS и Android evidence.
8. Сообщить изменённые каноны, адаптеры, wiring, проверки и остаточные риски.

Выбрать нативные invocation и role bindings по
[`runtime-adapters`](../../../workflow/rules/runtime-adapters.md).

Не применять для продуктового кода. Не создавать коммит без явной просьбы.
