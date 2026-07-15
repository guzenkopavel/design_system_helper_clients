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
