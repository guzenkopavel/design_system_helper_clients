---
name: plan
description: Создать change-aware self-contained platform plan. Использовать только по явному вызову plan с платформой, фичей и optional change ID; iOS поддержан, Android блокируется до записей.
---

# Plan

Полностью выполнить [`workflow/phases/plan.md`](../../../workflow/phases/plan.md).

1. Разобрать `$plan <platform> <feature> [--change <change-id>]`; missing/unsafe,
   unknown/Android и ambiguous omitted change блокируются до записей.
2. Потребовать валидный `specified` package по новой `changes/<change-id>/`
   identity; legacy-root fallback запрещён.
3. Последовательно выполнить read-only context/boundary review и передать
   единоличное владение `plan/` роли `implementation-planner`.
4. Revalidate/refine scopes до `planned`, recompute exact lifecycle rule union и
   загрузить plan profile; после `planned` scopes не расширять.
5. Создать README и contiguous tasks с `Status: pending`, `Evidence: none`, DAG,
   paths, inline contracts и focused checks.
   Для code/TDD/test/performance rules указать команды, budgets и finite
   watchdog limits.
6. Вычислить counts и запустить validator в `plan` mode с `--change`.
7. Сохранить `planned` только при green; иначе вернуть `specified`.

Manual-only. Не писать production code и не коммитить.
