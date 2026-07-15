# Android scope

Этот каталог принадлежит Android-клиенту. Общие правила наследуются из
[`../AGENTS.md`](../AGENTS.md).

Платформенные workflow-правила, скрипты и проверки размещать внутри `Android/`,
если они неприменимы к iOS. Изменение общего контракта считать
`cross-platform` и проверять также iOS-срез.

Implementation specs хранить в [`specs/`](specs/). Режим `product-backed`
разрешён только после `READY`/`APPROVED` общей спеки из
[`../specs/product/`](../specs/product/). Режим `technical-only` без общей спеки
разрешён только при `Product impact assessment: NONE` с evidence неизменности
observable behavior, REQ и AC; иначе перейти в product elaboration.

Android adapter поддерживает `propose`, `plan`, `implement`. Канон находится в
[`workflow/`](workflow/); Compose и multiplatform выбираются отдельными scopes.
`verify` и implementation archive пока возвращают `NOT IMPLEMENTED` до записи;
iOS rules не применять. Product archive остаётся отдельным shared lifecycle.

Перед разрешённым commit общий staged gate применяет Android `pre_commit`
profile из [`workflow/platform-contract.json`](workflow/platform-contract.json)
и addendum
[`workflow/phases/pre-commit-check.md`](workflow/phases/pre-commit-check.md).
Локальные SDK/credential/keystore файлы не читаются и не допускаются в index;
команды Gradle выбираются только по обнаруженному проекту и task evidence.
