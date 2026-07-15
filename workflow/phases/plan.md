---
phase: plan
writes_artifacts:
  - <platform>/specs/<feature>/plan/README.md
  - <platform>/specs/<feature>/plan/task-NNN.md
requires_verification: focused
recommended_roles:
  - repo-navigator
  - implementation-planner
---

# Phase: Plan

Преобразовать `specified` implementation package одной платформы в исполнимый
план. Production code не писать.

## Gate

Форма: `plan <platform> <feature>`. Platform и feature обязательны. Runtime
выбирает зарегистрированный adapter; unavailable adapter блокирует любые записи.

До planning требуются:

- совпадающие `platform` и `feature` в `meta.json`;
- `status: specified`;
- допустимый product-backed или technical-only intake;
- закрытые blocking questions;
- обязательный для tier design и verification mapping.

## Workflow

1. `repo-navigator` возвращает компактный read-only packet и отличает реальные
   пути от greenfield-предложений.
2. Выбранный platform boundary guard проверяет placement без записи.
3. `implementation-planner` единолично создаёт `plan/README.md` и задачи.
4. Построить DAG. Каждая задача:
   - ровно один layer;
   - ≤2 ideal dev-days до множителей;
   - явные files/zones и пометка `existing` либо `proposed`;
   - inline релевантные shared/platform requirement и AC context;
   - dependencies, goal, steps, verification, expected result, out of scope.
5. UI tasks включают simulator evidence, accessibility, design-system и
   selector checks. Risky/reversible boundary получает checkpoint.
6. Оценки — range для выбранной платформы с явными assumptions и mobile
   multipliers. Не объединять оценки разных платформ.
7. Выполнить `workflow/scripts/workflow-reflection.py plan`, записать candidate
   `status: planned`, `tasks_total: N`. Валидатор проверяет нумерацию и sections;
   при ошибке coordinator возвращает `specified` и `tasks_total: 0`.

Не превращать open question в задачу с выдуманным решением. Spec gaps возвращать
в propose, а behavioral gaps — в product elaboration.
