# Verification method matrix

Этот документ выбирает методы проверки; lifecycle, статусы и требования к
evidence определяет [`verification-evidence.md`](verification-evidence.md).
Matrix не создаёт второй SSOT и не ослабляет точные `PASS/FAIL/UNKNOWN` gates.

| Риск | Минимальный метод | Дополнение при высокой цене ошибки |
|---|---|---|
| Pure logic / state transition | unit/parameterized test | property or mutation-oriented cases |
| Module boundary / serialization | contract or integration test | compatibility fixture |
| Persistence / networking | deterministic integration with controlled boundary | failure/retry/offline runtime scenario |
| UI state and interaction | state test plus accessibility assertions | runtime UI scenario or automation |
| Concurrency / lifecycle | deterministic cancellation/ordering test | stress/run-loop diagnostics with bounded repeats |
| Performance | measured baseline and repeated comparable samples | profiling trace and budget comparison |
| Build/config/package | clean targeted build or package test | consumer integration and CI-equivalent run |
| Localization/accessibility | static checks plus representative runtime cases | locale/content-size/assistive-technology matrix |

Каждый platform AC получает ровно одну primary row в `verification.md`; несколько
методов перечисляются в одной строке или evidence-пакете. Метод должен проверять
наблюдаемый контракт, а не факт вызова mock. Неприменимый высокий уровень
обосновывается; отсутствие доступного окружения даёт UNKNOWN, не PASS.

Verify независимо пересобирает matrix из выбранных engineering scopes и fresh
repository evidence. Plan может задать budget/команду, но не предрешает статус.
