# iOS engineering rules — RED/GREEN evidence

## RED baseline

Перед изменением отсутствовали ровно 20 запрошенных канонов и машинный phase
profile contract.

Common — 8 missing files:

1. `workflow/rules/coding-standards.md`
2. `workflow/rules/code-comments.md`
3. `workflow/rules/tdd-first.md`
4. `workflow/rules/test-execution.md`
5. `workflow/rules/verification-matrix.md`
6. `workflow/rules/git-conventions.md`
7. `workflow/rules/branching.md`
8. `workflow/rules/developer-experience.md`

iOS — 12 missing files:

1. `iOS/workflow/rules/swift-style.md`
2. `iOS/workflow/rules/app-development.md`
3. `iOS/workflow/rules/package-development.md`
4. `iOS/workflow/rules/simulator.md`
5. `iOS/workflow/rules/performance.md`
6. `iOS/workflow/rules/performance/app-launch.md`
7. `iOS/workflow/rules/performance/concurrency.md`
8. `iOS/workflow/rules/performance/measure-first.md`
9. `iOS/workflow/rules/performance/memory.md`
10. `iOS/workflow/rules/performance/networking.md`
11. `iOS/workflow/rules/performance/profiling.md`
12. `iOS/workflow/rules/performance/swiftui-rendering.md`

Существующий `iOS/workflow/platform-contract.json` не содержал
`phase_rule_profiles` и `scope_rule_profiles`; `rule_files` был flat list,
поэтому phase/scope selection и selective fingerprint были невозможны.
Simulator concept намеренно адаптирован как resource-safe `simulator.md`, без
утверждения о существовании локального simulator pool/tooling.

## GREEN

- Добавлены 8 platform-neutral common canons и bounded
  `workflow/scripts/test-watchdog.sh`.
- Добавлены 12 iOS canons; существующие architecture, concurrency, testing,
  accessibility, design-system, localization, Xcode и SDK pitfalls расширены.
- Adapter содержит exact `propose/plan/implement/verify` phase bases, named
  selective scopes и полный catalog. `platform_rule_profiles.py` является
  единым resolver для retrieval и validator.
- Package meta хранит sorted `engineering_scopes` и exact lifecycle
  `applicable_rule_files`; unknown/missing/extra/unsafe значения дают RED.
- Plan seals both arrays in fingerprinted `plan/rule-selection.json`; downstream
  add/remove and snapshot tampering give RED.
- Design covers every selected scope exactly once. A Plan-added scope without
  architecture-designer re-entry gives RED.
- Tasks declare explicit scope subsets; task union covers the sealed package and
  adapter conditional checks apply regardless of task Layer.
- Fingerprint не читает raw adapter или flat catalog. Он включает exact rules и
  semantic projection identity/boundaries, all phase bases и только selected
  scope rule/task-check mappings.
- Retrieval file suffixes принадлежат adapter и входят в semantic projection;
  common resolver не hardcode'ит Swift/Xcode или будущий Android toolchain.
- Propose выбирает scopes; Plan может refine/add до `planned`; Implement/Verify
  используют неизменные scopes. Nontrivial checks имеют finite watchdog budget.

## Pressure combinations

### 1. UI + concurrency через четыре фазы

Resolver для каждой из `propose`, `plan`, `implement`, `verify` возвращает свой
base и deduplicated union scopes `ui, concurrency`. UI обязательно включает
accessibility, design-system, UI test spec/runtime simulator и MVVM; concurrency
включает correctness и performance concurrency lenses. Отдельный localization
scope не появляется неявно. Flat performance corpus не загружается.
Test-layer UI automation without simulator/accessibility/design-system checks
and a localization-tagged resource task without localization check give RED.

### 2. Package + networking + performance

`package` добавляет package boundary, DI/errors/types и unit-testing;
`networking` — только networking performance lens; `performance` — только
index, measure-first и profiling. Topic rules `startup`, `memory`, `rendering`
не загружаются без своих scopes. Harness lint проверяет эти dependencies.

### 3. Delivery + developer experience

Оба scopes условны. Git/branch rules сохраняют no-commit/no-destructive default
и требуют отдельной delivery authorization. DX измеряет feedback loop, но не
даёт права менять dependencies, ветку или external state. Propose/Plan могут
записать эти scopes, Implement не выполняет случайный commit.

### 4. Android и common isolation

Android не имеет adapter: lifecycle resolver блокирует `NOT IMPLEMENTED` до
package discovery/writes. Common rules не содержат Swift, Xcode, Simulator или
Apple SDK assertions; iOS paths находятся только в iOS adapter/addenda. Будущий
Android adapter обязан выбрать собственные rules и scopes.

Greenfield retrieval доказывает, что adapter-owned always-include glob находит
реальный project/package config без feature-name match. Suffixes и build-noise
exclusions также adapter-owned.

### 5. Selective fingerprint

Self-tests фиксируют RED после изменения выбранного application rule. Изменение
content и порядка mapping невыбранного performance scope остаётся GREEN.
Изменение task/design/verification/evidence по-прежнему делает state stale.

### 6. Watchdog

`test-watchdog.sh --self-test` проверяет: command PASS; исходный non-zero exit;
output cap; stall termination; maximum runtime termination. Exit codes
различаются, дочернее process tree получает cleanup, временный log удаляется.

### 7. Verify production guard

Pre-verifier baseline сохраняет pre-existing dirty state. Новое scoped verifier
evidence и verification fields дают GREEN; mutation production, task/plan,
selected rule, existing task evidence или unrelated post-baseline file даёт RED.
Task и Verify checks требуют coordinator-held SHA-256 исходного baseline;
перезапись baseline с recomputed hashes/permissions и изменение Git index state
вне scope дают RED.

## Deterministic checks

- `validate-platform-change.py --self-test` — lifecycle/profile/fingerprint PASS;
- `validate-implementation-scope.py --self-test` — task scope и Verify
  production write guard PASS;
- `capture-verification-state.py --self-test` — selective staleness PASS;
- `archive-change.py --self-test` — relocation/receipt/archive PASS;
- `find-platform-context.py --self-test` — greenfield always-include context PASS;
- `test-watchdog.sh --self-test` — pass/fail/output/stall/max PASS;
- profile pressure resolver — UI+concurrency, package+networking+performance и
  delivery+DX PASS;
- Android propose validation — `NOT IMPLEMENTED`, exit 4, no files written;
- `harness-lint.py --warn-as-error` — grade A, 0 critical, 0 warnings;
- `py_compile`, `bash -n`, `git diff --check` и quick validation семи изменённых
  workflow skills — PASS.

## Residual risks

Реальные application targets, schemes, Swift language mode, supported runtimes,
test commands и performance budgets пока не существуют или не доказаны
конфигурацией. Rules требуют discovery и маркируют greenfield defaults
provisional; harness self-tests не заменяют build/runtime evidence будущего
production change.

`plan/rule-selection.json` является consistency lock внутри repository, но не
внешним доказательством истории против coordinated total rewrite между разными
invocations. Такая гарантия потребовала бы нового публичного authority contract:
explicit token handoff, trusted external store или commit/ref.
