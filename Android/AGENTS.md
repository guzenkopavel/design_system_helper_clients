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

Android adapter поддерживает `propose`, `plan`, `implement`, `verify` и
implementation archive. Канон находится в [`workflow/`](workflow/); Compose и
multiplatform выбираются отдельными scopes. Verify обнаруживает repository
commands/infrastructure и не меняет production; archive требует fresh Android
fingerprint. iOS rules не применять. Product archive остаётся отдельным shared
lifecycle.

Для v1 common modularity и
[`architecture/modularization.md`](workflow/rules/architecture/modularization.md)
входят в base Propose/Plan/Implement/Verify независимо от optional `module`
scope. Новые cohesive feature/data/network/storage/reusable UI capabilities по
strong default получают обнаруженный Gradle Android/Kotlin module; application
module содержит только entry/root navigation/lifecycle/DI/config/resources и
composition. Folder/package name не является module. Deviation требует точного
settings/build constraint, typed seam и objective migration trigger.
Registry-anchored v0 выполняет только historical task paths/checks; v1
application-module composition rule к нему ретроактивно не применяется,
ownership не расширяется.

Product-backed `ui` требует READY `platform-ux.md`, owner —
`android-ux-designer`. Material 3 baseline обязателен; M3 Expressive/dynamic
color допустимы только с repository/product evidence и accessible fallback.

Для `$deep-code-review ... android ...` применять общий read-only контракт и
[`workflow/phases/deep-code-review.md`](workflow/phases/deep-code-review.md), не
предполагая Compose/Gradle conventions без repository evidence. После отдельного
fix вернуть route `$verify android ...`; review не заявляет fixed/verified до
успешного отдельного Implement + Verify.

Перед разрешённым commit общий staged gate применяет Android `pre_commit`
profile из [`workflow/platform-contract.json`](workflow/platform-contract.json)
и addendum
[`workflow/phases/pre-commit-check.md`](workflow/phases/pre-commit-check.md).
Локальные SDK/credential/keystore файлы не читаются и не допускаются в index;
команды Gradle выбираются только по обнаруженному проекту и task evidence.
