# Concurrent work lanes — test evidence

## Change plan

- **Тип/операция:** modify common orchestration rule, lifecycle phases/skills,
  guards, tracked hook wiring, process map и root documentation.
- **Scope:** cross-platform.
- **Канонический владелец:** independent lane semantics находится в
  `workflow/rules/orchestration-core.md`; implementation, reconciliation и
  delivery rules применяют этот контракт без собственного определения lane.
- **Инварианты:** single writer, без production/package staging/commit/push;
  selected mutable/read/control-plane projection fail-closed, disjoint state не
  присваивается lane.
- **Agent roster:** no-impact — роли и их write authority не менялись.
- **Runtime adapters:** update — tracked Git hook явно вызывает generic
  `--hook` integrity mode; Claude/Cursor/OpenCode bindings и platform contracts
  не изменялись.
- **Platform addenda:** no-impact — iOS/Android используют один общий lane
  алгоритм; SDK/build commands не менялись.

## RED

На исходном коде подтверждены три системных отказа:

1. Task/Verify baseline schema v2 снимала весь git-visible tree, global status,
   index и HEAD diff, поэтому Android/product/unrelated commit инвалидировали
   независимую iOS task lane и наоборот.
2. Reconcile guard сохранял full repository snapshot, global index fingerprint
   и HEAD identity, поэтому disjoint package/platform/product/index/commit
   блокировали выбранную reconciliation identity.
3. `pre-commit-check.py --staged` не связывал staged index с exact intended set,
   а production trail выбирал первого найденного owner; extra/missing staged
   paths и cross-package ownership ambiguity не имели отдельного fail-closed
   контракта.

## GREEN

- `validate-implementation-scope.py` пишет schema v3 с identity и
  `lane_projection`: selected package, task/realized Paths, Read-only context,
  shared spec, applicable rules, adapter и common/platform control plane.
  Files/status/index сравниваются только внутри projection; global HEAD lock
  удалён, SHA seal и selected index drift сохранены.
- `reconcile-implementation.py` хранит private `0600` scoped projection и exact
  projected index. Disjoint work и unrelated commit допускаются, selected
  production/package/read/control-plane drift остаётся invalid.
- `validate-platform-change.py` блокирует omitted `--change` при нескольких
  active либо partial/unclassified siblings и предоставляет полный active
  package ownership preflight.
- Implement baseline, Reconcile и pre-commit блокируют production Path с owners
  из нескольких active packages; overlapping sequential tasks одного package
  не считаются cross-package ambiguity.
- Канонический pre-commit принимает repeatable exact `--path`; staged set обязан
  совпасть полностью, включая обе стороны rename/copy. Exact PASS создаёт
  private `0700`/`0600` short-lived receipt вне repo. Runtime hook проверяет его
  non-consuming, tracked `--hook` потребляет one-shot и повторяет integrity.
- Единый `platform_path_ownership.py` нормализует writable paths и запрещает
  file/directory/proposed-child symlink traversal в Plan, Implement, Reconcile и
  pre-commit для обеих платформ.
- Active namespace inventory классифицирует каждый direct child fail-closed;
  junk sibling блокирует omission, но explicit корректный `--change` продолжает
  независимую lane.
- Единый `git_change_paths.py` разделяет delivery identity и write authority:
  rename old/new mutable, copy source+destination входят в identity, но source
  unchanged read-only, destination mutable/task-covered. Pair выбирается только
  explicit intended, identical repository files не расширяют identity.

## REFACTOR pressure matrix

1. iOS task/verify и Android task/verify принимают disjoint platform/product/
   feature dirty, unrelated staged index и unrelated commit; reverse direction
   симметрична.
2. Selected task Path, package, shared spec, applicable rule, adapter или common/
   platform control plane drift даёт INVALID; selected-lane index-only drift
   также блокируется.
3. Reconcile принимает disjoint Android/iOS/package/product/commit и блокирует
   изменение intended path либо watched dependency.
4. Два disjoint package одной platform работают с explicit `--change`; omission
   при нескольких или partial sibling блокируется.
5. Pre-commit exact intended A проходит с unrelated unstaged state; extra staged
   B, missing intended, unsafe path и неполная rename/copy дают FAIL.
6. Duplicate active package owner одного production boundary даёт FAIL во всех
   трёх preflight boundaries.
7. Real iOS/Android registry-anchored v0 packages остаются VALID; предыдущий
   lifecycle-flow-hardening suite остаётся green.
8. Receipt pressure: absent, stale, malformed, wrong mode, symlink, wrong repo,
   fingerprint/path mismatch и replay дают FAIL; два runtime preview не
   потребляют receipt, tracked consumption проходит ровно один раз.
9. Writable path pressure симметричен для iOS/Android: regular file и safe
   proposed child проходят, file symlink, directory symlink и proposed child
   через symlink ancestor блокируются.
10. Exact tombstone-only sibling допускает omission; junk file, symlink child и
    tombstone с extra state блокируют omission, explicit valid change проходит.
11. Copy E2E проходит Reconcile inspect/start/check, staging, exact gate,
    non-consuming preview и one-shot tracked consumption. Missing source/dest,
    replay, cross-adapter source, два explicit same-adapter peers и source reuse
    дают FAIL; один explicit peer детерминированно проходит даже при других
    identical iOS/Android files.
12. Receipt JSON отклоняет `NaN`, `Infinity`, `-Infinity`, boolean и иные
    non-finite timestamps до TTL/fingerprint acceptance.
13. Copy source exactness проверена напрямую, в Reconcile inspect/check и
    pre-commit: staged content с восстановленным HEAD worktree, cached mode-only,
    index deletion, unstaged content и synthetic unmerged stages дают FAIL;
    единственная regular stage-0 entry с HEAD-equal mode/blob проходит.

## Root documentation dispositions

- **README.md:** `no-impact` — top-level clients/capabilities/entrypoints не
  изменились; generated block должен остаться idempotent.
- **workflow.md:** `update` — описаны schema v3 scoped guards и exact intended
  delivery binding.
- **deep-info.md:** `update` — обновлены baseline/index algorithms, scoped
  Reconcile, canonical path ownership и receipt handshake hooks.

## Platform evidence

- **iOS:** общий synthetic pressure использует iOS identity/production boundary
  и принимает disjoint Android lane; real v0 package валидируется отдельно.
- **Android:** reverse synthetic pressure принимает disjoint iOS lane; adapter
  control plane остаётся watched; real v0 package валидируется отдельно.

## Проверки

- `validate-implementation-scope.py --self-test`: PASS.
- `validate-platform-change.py --self-test`: PASS.
- `reconcile-implementation.py --self-test`: PASS.
- `pre-commit-check.py --self-test`: PASS.
- `platform_path_ownership.py --self-test`: PASS.
- `git_change_paths.py --self-test`: PASS.
- Dependent `find-platform-context.py`, `hook-runner.py` и
  `capture-verification-state.py`: self-tests PASS.
- Existing lifecycle hardening: `artifact_language.py`,
  `validate-product-spec.py`, `archive-change.py`: self-tests PASS.
- Real registry-anchored packages:
  `validate-platform-change.py --platform ios|android --feature
  client-bootstrap --change initial-scaffold --mode implement`: оба `VALID`.
- `python3 -m py_compile` для затронутых Python modules: PASS.
- `harness-docs.py --self-test`: PASS; render изменил только generated inventory
  `deep-info.md`, повторный render сообщил `changed: []`; check `PASS`, errors
  `[]`.
- `harness-lint.py --self-test`: PASS; финальный JSON grade `A`, critical `0`,
  warnings `0`, findings `[]`.
- `git diff --check`: PASS.

## Остаточное ограничение

Persistent lane locks намеренно не создаются. Race с archive остаётся
остаточным риском и закрывается существующими fail-closed identity/archive
gates при следующем machine boundary, а не глобальной блокировкой репозитория.

Harness auditor выполняется отдельно от implementation-writer.
