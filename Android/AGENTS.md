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

Общий propose/plan/implement/verify/archive contract существует, но Android
adapter/architecture ещё не реализованы. Любой Android implementation-lifecycle
вызов завершается `NOT IMPLEMENTED` до записи artifacts; iOS rules в Android
scope не применять. Product archive требует явную Android disposition с
evidence даже при отсутствии adapter.
