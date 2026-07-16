# iOS scope

Этот каталог принадлежит iOS-клиенту. Общие правила наследуются из
[`../AGENTS.md`](../AGENTS.md).

Платформенные workflow-правила, скрипты и проверки размещать внутри `iOS/`,
если они неприменимы к Android. Изменение общего контракта считать
`cross-platform` и проверять также Android-срез.

Implementation specs хранить в [`specs/`](specs/). Режим `product-backed`
разрешён только после `READY`/`APPROVED` общей спеки из
[`../specs/product/`](../specs/product/). Режим `technical-only` без общей спеки
разрешён только при `Product impact assessment: NONE` с evidence неизменности
observable behavior, REQ и AC; иначе перейти в product elaboration.

Платформенный flow запускается как `$propose ios <feature> [--change ...]` →
`$plan` → `$implement` → `$verify` → `$archive implementation`. Активный пакет
живёт в `specs/<feature>/changes/<change-id>/`. Применять
[`workflow/phases`](workflow/phases/) и
[`workflow/rules`](workflow/rules/) как addenda к общему процессу. До перехода
между lifecycle states запускать общий validator; production scope проверять
baseline/check guard. Product archive остаётся общей отдельной операцией.

Product-backed `ui` требует READY `platform-ux.md`, owner — `ios-ux-designer`.
Он подтверждает SDK/deployment/components, system-first Liquid Glass и fallback;
не меняет shared product или остальные package artifacts.

Индекс addenda и rule profiles: [`workflow/README.md`](workflow/README.md).

iOS adapter выбирает phase base и только evidence-selected engineering scopes.
Точный lifecycle union хранится в meta и участвует в verification fingerprint;
невыбранный corpus не загружается и не делает evidence stale. Реальные Xcode,
Swift language mode, targets, schemes и simulator runtime всегда обнаруживаются.

Для v1 common modularity и
[`package-development.md`](workflow/rules/package-development.md) входят в base
Propose/Plan/Implement/Verify независимо от optional `package` scope. Новая
feature/data/network/storage/reusable UI capability по strong default получает
обнаруженный Swift package/target или Xcode target; app target оставляет только
entry/lifecycle/root navigation/DI/config/resources и composition. Folder не
заменяет target/package. Deviation требует точного project constraint, typed
seam и objective migration trigger.
Registry-anchored v0 выполняет только historical task paths/checks; v1 app-target
composition rule к нему ретроактивно не применяется, ownership не расширяется.

Для `$deep-code-review ... ios ...` применять общий read-only контракт и
[`workflow/phases/deep-code-review.md`](workflow/phases/deep-code-review.md).
После отдельного lifecycle fix fresh terminal evidence получает `$verify ios`;
сам review ничего не исправляет.

Перед разрешённым commit общий staged gate применяет iOS `pre_commit` profile из
[`workflow/platform-contract.json`](workflow/platform-contract.json) и addendum
[`workflow/phases/pre-commit-check.md`](workflow/phases/pre-commit-check.md).
Project/security edits разрешаются pre-tool guard только при покрытии active
task с явными engineering scopes; pre-edit не требует ещё не созданный
post-edit evidence. Секреты и signing material не читаются и не допускаются в
index.
