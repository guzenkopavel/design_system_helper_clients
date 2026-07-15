# Common harness layer

Общие правила и фазы живут в [`../../workflow/`](../../workflow/). Portable
skills живут в [`../../.agents/skills/`](../../.agents/skills/). Runtime
bindings описаны в
[`runtime-adapters.md`](../../workflow/rules/runtime-adapters.md).

Общий слой не должен предполагать конкретный SDK или build tool одной платформы.

Общий продуктовый контракт для клиентов хранится в
[`specs/product/`](../../specs/product/). Его доводят до `READY` portable skills
`brainstorming`, `discovery` и `elaborate`; правила границы описаны в
[`specification-layers.md`](../../workflow/rules/specification-layers.md).
Для UI/interaction scope пакет включает shared UX; `READY` невозможен без
applicable reviews и явного human product approval.

После fan-out общие propose/plan/implement/verify/archive phases, lifecycle, templates, roles и
system-design остаются в `workflow/`. Они не содержат Swift, Xcode или Apple SDK.
Public invocation всегда передаёт `<platform> <feature>`.

Platform package identity дополняется strict kebab-case `change_id`; active
discovery смотрит только `changes/`, а product discovery исключает `_archive`.

Adapter catalog распределяется по exact phase bases и named engineering scopes.
Package фиксирует evidence-selected scopes и полный lifecycle union; общий
resolver используется retrieval, validator и fingerprint logic. Условные
delivery/DX rules не дают права коммитить или менять ветки.

Общий pre-commit gate анализирует staged blobs, fingerprint и task trail; общий
hook runner защищает dangerous Git и edit boundaries. Платформенные suffix/glob
категории принадлежат adapter `pre_commit`, а runtime bindings остаются thin.
