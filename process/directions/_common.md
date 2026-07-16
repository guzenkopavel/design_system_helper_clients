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
applicable reviews и явного human product approval. После approval Elaborate
запускает шесть isolated fresh lens contexts на одном fingerprint, coordinator
сохраняет runtime invocation evidence и агрегирует PASS либо durable non-green
receipt; JSON attestation не заменяет runtime audit. Downstream принимает package только через
`validate-product-spec.py check`.

После fan-out общие propose/plan/implement/verify/archive phases, lifecycle, templates, roles и
system-design остаются в `workflow/`. Они не содержат Swift, Xcode или Apple SDK.
Public invocation всегда передаёт `<platform> <feature>`.

Общий `reconcile-implementation` перед staging принимает явный production path
set, делит его на независимые вызовы по каждой platform/feature/change identity
и разрешает только guarded package repair. Platform addenda выбирают SDK/tooling evidence;
production/shared product/index остаются read-only.

Общий `deep-code-review` задаёт read-only modes, finding schema, feedback triage,
bug proof и security scan. Для `review|feedback|bug` он также требует
`<platform> <feature>` и подключает addendum выбранного клиента; `security`
сканирует только harness surfaces без platform identity и без изменений.

Platform package identity дополняется strict kebab-case `change_id`; active
discovery смотрит только `changes/`, а product discovery исключает `_archive`.

Adapter catalog распределяется по exact phase bases и named engineering scopes.
Package фиксирует evidence-selected scopes и полный lifecycle union; общий
resolver используется retrieval, validator и fingerprint logic. Условные
delivery/DX rules не дают права коммитить или менять ветки.

Новые implementation packages используют versioned modularity contract v1.
Packages без version field остаются legacy v0 только при exact identity/hash
match с [`modularity-v0.json`](../../workflow/compatibility/modularity-v0.json).
Они могут завершить Implement/Verify/Archive с исторической projection, но
Propose/Plan, registry mismatch или drift design/meta/plan/tasks требуют
отдельного migration/new change package. Нормализация anchor разрешает менять
только task Status/Evidence values и lifecycle meta/evidence.
Сам registry защищён code-pinned canonical digest и exact ordered identities;
registry-only extension не выдаёт trust. Legacy meta допускает только exact
historical keys, где mutable лишь status/tasks_done/problems/verification state.

Общий pre-commit gate анализирует staged blobs, fingerprint и task trail; общий
hook runner защищает dangerous Git и edit boundaries. Платформенные suffix/glob
категории принадлежат adapter `pre_commit`, а runtime bindings остаются thin.
