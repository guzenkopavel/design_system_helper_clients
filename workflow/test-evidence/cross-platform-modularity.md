# Cross-platform modularity — RED → GREEN → REFACTOR

Scope: hard cross-platform harness contract. Native production code and runtime
skill bindings не менялись. iOS и Android проверяются раздельно; green одной
платформы не считается evidence для другой.

## RED baseline

До изменения narrative boundary мог пройти без machine-readable capability
signals, фактического physical unit и проверяемого repository evidence. App
target/module можно было описать как временное deviation, а folder/layer — как
будущий module/package. Старые active packages при прямом добавлении новых
mandatory fields потеряли бы совместимость.

## GREEN — exact v1 contract

Канон `workflow/rules/system-design/modularity.md` и adapters задают:

- exact capability triggers: `independent-feature`, `domain-data`, `network`,
  `persistence`, `reusable-ui`, integer `consumers`, `independent-ownership`;
- exact app-shell allowlist: `entry-points, lifecycle, root-routing,
  dependency-wiring, platform-configuration, target-resources`;
- exact app-shell capability ownership `none`;
- the two exact app-shell rows are the only permitted shell claims; every other
  free-form decision field rejects every standalone `app`, `application`,
  `shell`, `target`, `module` token, including possessives and reordered
  phrases, independently of ownership verbs;
- `Repository evidence` как `;`-separated список существующих безопасных
  repo-relative files/directories;
- physical units только из platform adapter и только non-application;
- `deviation` только в existing/discovered non-application unit с typed seam и
  objective migration trigger;
- `not-applicable` только когда все boolean triggers `no`, consumers ≤ 1 и
  independent ownership отсутствует;
- Verify fields для dependency graph, public API/visibility, module tests,
  consumer integration/build и app-shell allowlist. В terminal modes все они
  должны быть `PASS`; недоступный tool/graph остаётся `UNKNOWN` и блокирует.

Folder/directory/layer/package-name не заменяет physical unit. App shell не
может владеть feature/domain/data/network/persistence/reusable-UI implementation
или mutable state ни при одном outcome.

## Real-adapter pressure

`validate-platform-change.py --self-test` загружает реальные
`iOS/workflow/platform-contract.json` и
`Android/workflow/platform-contract.json`, а не только synthetic fixture.

Для каждой платформы отдельно проверяются:

1. broad capability + adapter isolation scope + proposed library unit +
   существующие project/adapter evidence paths → `PASS`;
2. both exact inverse phrases on both adapters → `BLOCK`:
   `Feature data network persistence implementation resides in the application
   shell.` and `The application shell is responsible for feature data network
   persistence implementation and mutable state.`; `lives in` and inverse
   `responsibility of` variants are also blocked;
3. reordered/possessive host variants `target of the app`, `app's target`,
   `executable target of the application`, `application host module`, `module
   belonging to the app`, `application composition shell` и `host shell of the
   app` with owns/resides/responsible/lives claims → `BLOCK` on both real
   adapters;
4. broad triggers под `not-applicable` → `BLOCK`;
5. folder-as-module/package bypass → `BLOCK`;
6. несуществующий evidence path → `BLOCK`;
7. adapter с application target/module среди physical units → schema `BLOCK`;
8. existing/discovered non-application deviation + typed seam/trigger → `PASS`;
9. tiny one-consumer `not-applicable` → `PASS`;
10. `UNKNOWN` modularity verification допустим во время Implement, но блокирует
   Verify.

iOS adapter разрешает только `Swift package`, `Swift package target` и
`non-application Xcode target`. Android adapter разрешает только `Gradle Android
library module` и `Gradle Kotlin library module`. Names, schemes, tasks и
commands по-прежнему должны обнаруживаться из repository.

## Versioned compatibility

Новые packages и adapters используют modularity contract v1; snapshot schema
v2 включает version в fingerprint. Missing package field означает v0 только при
exact match tracked `workflow/compatibility/modularity-v0.json`.

Registry allowlist содержит ровно active identities
`iOS/client-bootstrap/initial-scaffold` и
`Android/client-bootstrap/initial-scaffold`. Для каждой записаны SHA-256:

- полного `design.md`;
- canonical immutable meta projection с identity/intake/product impact/scopes/
  rules/snapshot/blocking_questions/tasks_total/design_gate и всеми остальными
  keys, кроме шести lifecycle-mutable fields;
- полного `plan/rule-selection.json` и `plan/README.md`;
- canonical sorted task graph. В task content нормализуются только значения
  exact `Status` и `Evidence`; filename, paths, scopes, dependencies, inline
  contract, commands и Boundary owner остаются immutable.

Common resolver code pin'ит canonical SHA-256 всего registry и ordered exact two
identity/path entries. Поэтому registry-only append/edit не расширяет trust.

Adversarial self-test фиксирует: unregistered sealed-looking identity BLOCK;
registered baseline PASS; append design, add/remove task, path/scope/dependency
change и meta scopes/rules/tasks_total change — BLOCK; только task
Status/Evidence + lifecycle meta/evidence — PASS. Validator применяет
historical phase projection/legacy checks лишь после anchor match. Propose/Plan,
unknown version и any immutable drift блокируются и маршрутизируются в new
migration change. Active iOS/Android packages проходят exact Implement без
изменений package files.
Extra meta key и изменение `blocking_questions` блокируются самим common
resolver во validator/find-context/reconcile callers. Fresh copied
`forged-v0` с корректно пересчитанной третьей registry entry блокируется и
validator, и harness lint по code-pinned trust anchor.

## REFACTOR и residual limitation

Common validator остаётся platform-neutral: unit types приходят из adapters, а
platform mechanics — из addenda. Machine gate доказывает schema, repository
path existence и profile parity, но не истинность архитектурного rationale и не
семантику dependency graph. Это остаётся обязанностью read-only platform
boundary guard и fresh Verify evidence.

## Executed checks

- `validate-platform-change.py --self-test` — PASS;
- `reconcile-implementation.py --self-test` — PASS, включая v0 aligned/drift;
- `harness-lint.py --self-test` и docs self-test — PASS;
- dependent lifecycle self-tests: archive, implementation scope, context
  discovery, verification-state capture и pre-commit — PASS;
- exact active iOS implement validation — `VALID`;
- exact active Android implement validation — `VALID`;
- `harness-docs.py render` и read-only `check --json` — PASS;
- `harness-lint.py --json` — grade A, 0 findings;
- Python compileall, `git diff --check` и forbidden-source scan — PASS.
