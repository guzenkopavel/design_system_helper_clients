---
phase: implement
writes_artifacts:
  - task-declared production paths
  - <platform>/specs/<feature>/changes/<change-id>/evidence/task-NNN.md
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
  - <platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md
requires_verification: focused
recommended_roles:
  - implementation-discovery
  - implementation-writer
---

# Phase: Implement

Require adapter `implement` capability before package discovery. A platform
without Verify capability completes tasks but remains non-terminal
`implementing` with verification pending.

Form: `implement <platform> <feature> [--change <change-id>] [--task task-NNN|--all]`.
Platform and feature are required. Resolve omitted change only when exactly one
active package exists. Missing `implement` capability, unknown platform,
traversal and ambiguity block before writes. Android is supported through its
adapter and finishes non-terminal when Verify capability is absent.

Accept only `planned` or `implementing`. Для каждой задачи выполнять один и тот
же короткий алгоритм:

1. Выбрать pending task с выполненными dependencies и перечитать только её
   self-contained contract, exact `Paths`, `Read-only context`, meta scopes,
   adapter и resolver-selected implement profile.
2. До writes снять selected-lane scope snapshot и удерживать его SHA-256 вне
   writer-accessible repository state. `INVALID` останавливает writes и сообщает
   exact selected-lane errors; не исправлять ради snapshot evidence предыдущей
   задачи или foreign lane.
3. При `VALID` передать единственному writer только compact task handoff. Не
   анализировать общий `git status`: disjoint dirty/index/commit другой identity
   не относится к выбранной lane.
4. Реализовать каждый `Implementation deliverables` только внутри task `Paths`,
   выполнить bounded focused checks и записать текущий task report по
   [`platform-task-evidence`](../templates/platform-task-evidence.md).
5. Выполнить scope check с coordinator-held SHA, затем и только затем отметить
   task `done` и пересчитать `tasks_done`.

`--all` повторяет алгоритм в DAG order и останавливается на первой ошибке.

If an explicit pre-delivery code set no longer matches task coverage or current
platform contracts, Implement does not silently repair the plan. Route that set
to `$reconcile-implementation` before staging; behavioral/shared impact returns
to product Discovery/Elaborate.

The `implementation-writer` runs in `platform-implementation` mode and treats
the task as the primary self-contained input. Для current v1 он реализует
каждый пункт `Implementation deliverables`; этот список определяет, что должно
появиться, но не расширяет write authority за task `Paths`. It may change only task-declared
production paths plus scoped package evidence/state. Use behavior-first/TDD,
the platform architecture/testing lenses, and no side features. Capture a scope
baseline before writes, retain the emitted SHA-256 token in coordinator memory
outside repository state, and pass it as `--expected-sha256` to the post-write
check. Every declared Path
must be inside adapter production roots and outside protected/excluded roots;
canonical ownership helper также запрещает symlink traversal для file,
directory и proposed-child boundaries; one valid Path never masks an invalid
sibling. Implement writes are limited to
task Paths, task/meta state, `evidence/task-NNN.md` and
`evidence/scope-baseline-task-NNN.json`; the writer must not rewrite that
coordinator-owned baseline. Guard использует independent task lane и не
присваивает себе unrelated staged/unstaged/untracked state другой
platform/feature/product lane.
Baseline schema v3 фиксирует algorithm `git-visible-lane-v1`: hash set состоит
из tracked и non-ignored untracked файлов только selected package, task Paths,
Read-only context, shared spec, applicable rules, adapter и common/platform
control plane. Ignored caches, `node_modules`, build output и disjoint dirty/
HEAD changes не входят в projection. Отдельный
`git-ls-files-stage-lane-v1` snapshot сохраняет exact selected-lane index entries
`path + mode + stage + blob_id`; любое index-only изменение блокирует task и
verify guard даже при одинаковых worktree bytes и porcelain XY. До baseline
cross-package owner ambiguity каждого task Path обязана дать fail-closed.

For product-backed UI tasks, reread immutable `platform-ux.md` and implement its
native language, appearance, accessibility/motion and fallback checks. Record
focused native appearance evidence without rewriting the artifact.

В exact direct-child `evidence/task-NNN.md` обязателен короткий русский `Итог`.
Без fences в `Технические доказательства` допустимы только safe path/change rows
и bounded exact repo-tooling command lines. Произвольный raw output сохранять в
fence или отдельном `.log`; любой иной текст остаётся authored и проверяется по
[`artifact-language`](../rules/artifact-language.md). Не переносить в report
общий git status или состояние foreign/disjoint lane.

Before the baseline, resolve `--phase implement` with the exact immutable scopes
from meta and require the returned lifecycle union to match
`applicable_rule_files`. Apply behavior-first/TDD, coding/comments and only the
resolver-selected platform scope rules. A nontrivial test/build command is
run through `workflow/scripts/test-watchdog.sh` using the plan budget; any
override records a reason and remains finite.

For `modularity_contract_version: 1`, the implement base applies common and
adapter modularity rules. Honor the sealed `Modularity decision`: do not put
feature/domain/data/network implementation or mutable state in the application
shell, do not treat folders as modules and do not widen a deviation beyond its
typed seam/task paths. Registry-anchored v0 instead receives only the
resolver-selected historical projection and adapter `legacy_task_checks`; it
may complete historical lifecycle task paths/status/evidence, but receives no
retroactive v1 decision/composition checks and cannot expand ownership or
immutable package structure.

Set `status: implementing` when work starts. Mark a task `done` and give it a
concrete package-relative evidence path only after focused checks pass and the
scope validator is green. Derive `tasks_done` from task files. Implement never
sets `verified`, never performs broad cleanup, destructive git or commit.

After failed verification, accept only the machine-coherent recovery state from
Verify: exact FAIL/UNKNOWN rows and `problems`, affected tasks reopened, null
terminal state. Reimplement those ready tasks, but leave final status assignment
to a fresh Verify run. When a recovery task passes focused evidence/scope and is
marked done, invalidate the old verification run before Implement validation:
reset every verification row to `pending`, clear `problems`, set
`verification_status: pending`, `verified_at: null`, `verification_state: null`
and preserve historical evidence files. Other reopened dependents stay pending.
Only a baseline captured in FAIL/UNKNOWN recovery may authorize this exact
`verification.md` write; initial implementation never may.
