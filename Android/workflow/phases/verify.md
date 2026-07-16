# Android addendum: Verify

Использовать общий [`verify`](../../../workflow/phases/verify.md) без изменения
production. Сохранить sealed `engineering_scopes`, `applicable_rule_files` и
`plan/rule-selection.json`. Для v1 Android verify profile содержит compatibility pair
`workflow/rules/test-execution.md` и
`workflow/rules/verification-matrix.md`, а также обязательные common
`workflow/rules/system-design/modularity.md` и platform
`Android/workflow/rules/architecture/modularization.md`. Для registry-anchored
v0 resolver выбирает historical profile без retroactive modularity pair и
добавляет только adapter `legacy_task_checks`; ownership/structure не
расширяются. Общий
`workflow/rules/verification-evidence.md`, общий verify phase и этот addendum
загружаются и fingerprinted напрямую как обязательные terminal contracts вне
sealed engineering union; это не расширяет `applicable_rule_files`.

Из repository и Plan обнаружить wrapper, settings, modules, plugins, variants,
available tasks, commands и необходимую runtime infrastructure. Не предполагать
module `app`, Compose, variant, Emulator, system Gradle или существование
`build`, `test`, `lint`, `connected*` task. Использовать exact selected scopes и
только реально обнаруженные команды; nontrivial command запускать через общий
watchdog с finite budget.

Каждый обязательный method получает fresh `PASS|FAIL|UNKNOWN`: недоступная
обязательная infrastructure — `UNKNOWN`, nonzero discovered command — `FAIL`,
а `PASS` требует concrete package evidence. `android-build-diagnostician`
разрешён только для read-only diagnosis результата, не для repair. Общий
verify-scope baseline/check запрещает production, task, plan, contract, adapter
и rule writes во время verifier pass.
Для product-backed UI проверить native appearance scenarios из
`platform-ux.md`; отсутствие нужного emulator/SDK/dependency даёт UNKNOWN.

Для v1 отдельно проверить realized Gradle/Kotlin/Android module graph, public
API/visibility, module-level tests, consumer integration/build и application-
module allowlist. Недоступный graph/tooling даёт UNKNOWN. Folder/package name
без physical module не считается isolation.
Для registry-anchored v0 выполнить только historical selected checks, включая
adapter `legacy_task_checks`; не добавлять v1 application-module/composition
assertions и не расширять ownership.
