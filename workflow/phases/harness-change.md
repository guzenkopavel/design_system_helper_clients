---
phase: harness-change
writes_artifacts:
  - canonical harness files
  - synchronized runtime adapters and process map
  - workflow/test-evidence/<name>.md for hard changes
requires_verification: focused
recommended_roles:
  - implementation-writer
  - harness-auditor
---

# Phase: Harness Change

Изменять сам харнес: правила, фазы, профили, skills, команды, роли, hooks,
скрипты, шаблоны и process map. Для продуктового кода эту фазу не применять.

## Процедура

### 0. Intake и locate

Заполнить [`../templates/harness-change.md`](../templates/harness-change.md).

1. Классифицировать тип сущности и операцию.
2. Определить scope по [`../rules/platform-scope.md`](../rules/platform-scope.md).
3. Найти владельца через [`../../process/README.md`](../../process/README.md).
4. Искать существующую механику по имени, назначению и синонимам.
5. Перечислить и просмотреть релевантные `scripts/`, skills и роли во всех
   затронутых scope.
6. Зафиксировать зависимости и инварианты, которые нельзя сломать.

### 1. Implement

Передать scoped change-plan роли `implementation-writer` как единственному
writer. Соблюдать [`../rules/memory-architecture.md`](../rules/memory-architecture.md):
знание менять в каноне, runtime binding — в адаптере.

Для нового жёсткого правила, skill или роли применить
[`writing-skills.md`](writing-skills.md). Для typo, link fix, index и
неинструктивной документации этот шаг можно пропустить.

Пройти wiring cascade:

- process map;
- agent roster;
- portable skill metadata и все runtime adapters;
- workflow index;
- root/platform `AGENTS.md` при изменении entry point или инварианта;
- test evidence для hard change.

### 2. Review

Применить [`harness-review.md`](harness-review.md): получить grade A от линтера и
вердикт `CLEAN` от `harness-auditor`.

Для `cross-platform` отдельно проверить iOS и Android. Общий green не заменяет
платформенные evidence.

### 3. Fix-loop

Передавать подтверждённые findings `implementation-writer`, повторять lint и
судительный аудит до green. Соблюдать bounded loop из
[`../rules/orchestration-core.md`](../rules/orchestration-core.md).

### 4. Report

Сообщить scope, изменённые каноны и адаптеры, wiring, проверки по платформам,
test evidence и остаточные риски. Не создавать коммит без явной просьбы.

Runtime binding выбирать по
[`../rules/runtime-adapters.md`](../rules/runtime-adapters.md). Если custom
subagent недоступен, использовать описанный там последовательный fallback и
отразить отсутствие независимого review в отчёте.
