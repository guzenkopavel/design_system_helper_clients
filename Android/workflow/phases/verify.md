# Android addendum: Verify

Использовать общий [`verify`](../../../workflow/phases/verify.md) без изменения
production. Сохранить sealed `engineering_scopes`, `applicable_rule_files` и
`plan/rule-selection.json`; Android verify profile состоит только из общих
`workflow/rules/test-execution.md` и
`workflow/rules/verification-matrix.md`. Общий
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
