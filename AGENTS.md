# AGENTS.md — вход в репозиторий мобильных клиентов

Репозиторий содержит два самостоятельных клиентских проекта:

- [`iOS/`](iOS/) — iOS-клиент;
- [`Android/`](Android/) — Android-клиент.

Общие правила и процедуры живут в [`workflow/`](workflow/). Платформенные
уточнения должны находиться внутри соответствующего корня, а не копироваться в
общий слой.

## Изменения харнеса

- Канонический процесс: [`workflow/README.md`](workflow/README.md).
- Карта сущностей и связей: [`process/README.md`](process/README.md).
- Runtime matrix: [`workflow/rules/runtime-adapters.md`](workflow/rules/runtime-adapters.md).
- Изменение харнеса: `harness-change` через нативный skill-вход runtime.
- Проверка харнеса: `harness-review` через нативный skill-вход runtime.
- Root docs: [`README.md`](README.md), [`workflow.md`](workflow.md),
  [`deep-info.md`](deep-info.md); канон impact/freshness:
  [`repository-documentation.md`](workflow/rules/repository-documentation.md).

Перед правкой харнеса определить scope: `common`, `ios`, `android` или
`cross-platform`. Для `cross-platform` отдельно проверить обе платформы и не
считать успешную проверку одной платформы доказательством для другой.

Каждый harness change указывает `update|no-impact + rationale` отдельно для
трёх root docs, затем выполняет `harness-docs.py render` и read-only `check`.
Generated blocks вручную не редактировать; root docs не владеют policy.

## Продуктовая проработка

- `brainstorming` исследует сырую идею и альтернативы;
- `discovery` создаёт общий product brief с draft screen/flow impact;
- `elaborate` добавляет применимый shared UX, review lenses и явный human
  approval, доводит пакет до `READY` и останавливается до fan-out.

Продуктовый SSOT для обоих клиентов находится в
[`specs/product/`](specs/product/). Platform implementation specs создаются в
[`iOS/specs/`](iOS/specs/) и [`Android/specs/`](Android/specs/). Режим
`product-backed` требует общий `READY`/`APPROVED`-контракт без копирования
REQ/AC. Режим `technical-only` без shared spec допустим только при доказанном
`Product impact assessment: NONE`; behavioral impact возвращает задачу в
product elaboration. Каноническая граница:
[`specification-layers.md`](workflow/rules/specification-layers.md).

Без явного product approval с evidence общий пакет остаётся
`DRAFT / PENDING APPROVAL` независимо от полноты остальных артефактов.

После approval все шесть product review lenses выполняются заново в отдельных
fresh `product-spec-reviewer` contexts на одном fingerprint и parent session;
coordinator хранит runtime invocation evidence. JSON attestation не является
доказательством isolation. Reviewer read-only и не пишет receipt/READY.
Same-context fallback — durable `UNKNOWN`; без fresh green
`review-verdicts.json` и `validate-product-spec.py check` platform fan-out
запрещён.

## Платформенная проработка

Для product-backed `ui` Propose последовательно создаёт conditional
`platform-ux.md` через adapter UX designer между specification и architecture.
Shared mood — calm/soft blue через semantic roles; iOS адаптирует его через
evidence-backed Liquid Glass, Android — Material 3 с conditional M3 Expressive.
Technical-only/non-UI packages artifact не требуют.

- `$propose <platform> <feature> [--change <change-id>]` создаёт change package;
- `$plan <platform> <feature> [--change <change-id>]` создаёт execution plan;
- `$implement <platform> <feature> [--change <change-id>]` выполняет ready tasks;
- `$verify <platform> <feature> [--change <change-id>]` фиксирует fresh evidence;
- `$reconcile-implementation <platform> <feature> [--change <change-id>]
  --path <repo-relative>...` до staging сверяет явный production set с package;
- `$archive implementation ...` и `$archive product ...` архивируют разные SSOT;
- platform и feature обязательны;
- iOS и Android поддерживают полный implementation lifecycle через собственные
  adapters и platform addenda;
- активный package живёт в adapter `package_root` и не копирует shared REQ/AC;
- downstream omission `--change` допустим только при одном active package.

Только `implement` пишет production code в task scope; `verify` не меняет
production. Общие lifecycle/system-design/archive правила находятся в
`workflow/`, платформенные детали — только в соответствующем корне.

Reconciliation никогда не пишет production/shared product/index. Shared
behavior `PRESENT`/`UNCERTAIN` возвращается в Discovery/Elaborate; cross-platform
set и несколько packages одной платформы обрабатываются независимыми запусками
по каждой platform/feature/change identity.

Каждый platform package хранит evidence-selected `engineering_scopes` и точный
derived `applicable_rule_files`. Propose выбирает scopes, Plan может уточнить их
до `planned`, Implement/Verify используют неизменный набор. Flat adapter catalog
не загружается глобально; nontrivial checks выполняются с finite watchdog.

## Deep code review

- `$deep-code-review review <platform> <feature> [--change ...]` выполняет
  evidence-driven read-only review;
- `feedback` перепроверяет входящие пункты по current code;
- `bug` не объявляет root cause без reproduction и evidence;
- `security [--json]` сканирует harness с полной redaction секретов;
- `fix`/`--fix`, unsafe paths, platform omission и ambiguous identity
  блокируются до чтения scope;
- skill не пишет production, package, evidence/meta, не запускает lifecycle и
  не делает commit/push.

После invocation validation каждый mode обязан выполнить machine guard
`deep-code-review-readonly-guard.py start`, а перед отчётом — `check`. Mutation
или неполное bounded coverage делает review недействительным; guard не revert
пользовательские изменения и хранит только private ephemeral state вне repo.

Общие finding schema и роли находятся в
[`deep-code-review.md`](workflow/phases/deep-code-review.md). Platform lenses
добавляются из соответствующего клиента. После отдельного исправления обе
платформы маршрутизируются в собственный `$verify`; review остаётся read-only и
не заявляет fixed/verified до отдельного успешного lifecycle.

## Инварианты

- Знание хранить в одном каноническом месте; адаптеры должны только связывать
  канон с конкретным runtime.
- Portable skills хранить в `.agents/skills/`; runtime-копии процесса не создавать.
- Не смешивать платформенные правила с общими без необходимости.
- Не коммитить и не публиковать изменения без явной просьбы пользователя.
- Человекочитаемые отчёты и документы писать на русском; код, пути и
  идентификаторы — на английском.

## Commit gate и hooks

Явная просьба о commit сначала фиксирует явный intended path set, выполняет
`$reconcile-implementation` отдельно для каждой затронутой
platform/feature/change identity и выдаёт report. Только затем разрешённый set
stage'ится и запускается portable
`$pre-commit-check` по staged index. Gate не выполняет staging, commit, push и не расширяет delivery
authorization. Канон: [`pre-commit-integrity.md`](workflow/rules/pre-commit-integrity.md).

Tracked Git hook находится в [`.githooks/pre-commit`](.githooks/pre-commit), а
runtime hooks делегируют общему
[`hook-runner.py`](workflow/hooks/hook-runner.py). Runtime hook может дать ранний
deny/warning, но обязательной границей остаётся Git hook после явной безопасной
активации `core.hooksPath`; автоматически менять `.git/config` запрещено.
