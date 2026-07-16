---
name: implement
description: Выполнить ready tasks platform package при поддержанной implement capability.
---

# Implement

Полностью выполнить [`workflow/phases/implement.md`](../../../workflow/phases/implement.md).

Форма: `$implement <platform> <feature> [--change <change-id>] [--task task-NNN|--all]`.
Проверить adapter/identity и package до записей. Через
`implementation-discovery` выбрать только ready pending task, сохранить scope
baseline, затем передать production writes единственной роли
`implementation-writer` в режиме `platform-implementation`. Загрузить exact
implement profile + неизменные meta scopes; flat rule catalog не загружать.
Nontrivial checks выполнять через `test-watchdog.sh` с plan budgets. После focused
evidence проверить scope с coordinator-held `--expected-sha256`, обновить task
status/evidence и derived `tasks_done`. SHA token из snapshot не записывать в
writer-accessible repo state и не передавать writer роли.
Scope допускает только каждый declared production Path и точные файлы
`evidence/task-NNN.md`, `evidence/scope-baseline-task-NNN.json`; mixed unsafe
Path и ambiguous owner из другого active package блокируют весь task. Canonical
ownership helper также блокирует symlink file/directory/proposed-child. Scoped
lane baseline охраняет выбранный package/Paths/read dependencies/control plane,
но не блокируется disjoint dirty/index/commit другой identity. Recovery после Verify обрабатывается только через
reopened tasks и точные problems/FAIL/UNKNOWN rows. После первого успешного
recovery task сбросить все verification rows/meta в pending/null, не удаляя
historical evidence; только recovery baseline разрешает запись verification.md.
Никогда не выставлять `verified`, не добавлять side features и не коммитить.

Manual-only; unsupported capability, unknown/ambiguous/unsafe identity
завершаются с нулём записей. Android dispatch выполняется через adapter.
