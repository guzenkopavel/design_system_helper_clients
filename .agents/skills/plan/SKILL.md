---
name: plan
description: Создать self-contained platform plan при поддержанной plan capability.
---

# Plan

Полностью выполнить [`workflow/phases/plan.md`](../../../workflow/phases/plan.md).

1. Разобрать `$plan <platform> <feature> [--change <change-id>]`; missing/unsafe,
   unsupported/unknown и ambiguous omitted change блокируются до записей.
2. Потребовать валидный `specified` package по новой `changes/<change-id>/`
   identity; legacy-root fallback запрещён.
   Feature-root `SPECIFICATION.md` использовать только как immutable baseline и
   до декомпозиции подтвердить полноту post-change `implementation-spec.md`.
3. Последовательно выполнить read-only context/boundary review и передать
   единоличное владение `plan/` роли `implementation-planner`.
4. Revalidate/refine scopes до `planned`, recompute exact lifecycle rule union и
   загрузить plan profile; после `planned` scopes не расширять.
5. Создать README и contiguous tasks с `Status: pending`, `Evidence: none`, DAG,
   writable production `Paths`, отдельным exact `Read-only context`, inline
   contracts, exact `Implementation deliverables` с минимум двумя конкретными
   top-level list items и focused checks. Deliverables фиксируют, что будет
   реализовано; `Steps` отдельно фиксирует способ выполнения. В mode=plan провалидировать adapter boundaries,
   existing/proposed classification, duplicates, ancestor overlaps и canonical
   no-symlink ownership для file/directory/proposed-child.
   Для code/TDD/test/performance rules указать команды, budgets и finite
   watchdog limits.
6. Вычислить counts и запустить validator в `plan` mode с `--change`.
7. Сохранить `planned` только при green; иначе вернуть `specified`.

Manual-only. Не писать production code и не коммитить.
