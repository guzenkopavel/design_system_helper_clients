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

Перед правкой харнеса определить scope: `common`, `ios`, `android` или
`cross-platform`. Для `cross-platform` отдельно проверить обе платформы и не
считать успешную проверку одной платформы доказательством для другой.

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

## Платформенная проработка

- `$propose <platform> <feature> [--change <change-id>]` создаёт change package;
- `$plan <platform> <feature> [--change <change-id>]` создаёт execution plan;
- `$implement <platform> <feature> [--change <change-id>]` выполняет ready tasks;
- `$verify <platform> <feature> [--change <change-id>]` фиксирует fresh evidence;
- `$archive implementation ...` и `$archive product ...` архивируют разные SSOT;
- platform и feature обязательны;
- iOS поддерживает полный lifecycle; Android — только `propose/plan/implement`,
  а `verify` и implementation archive блокируются capability gate до записи;
- активный package живёт в adapter `package_root` и не копирует shared REQ/AC;
- downstream omission `--change` допустим только при одном active package.

Только `implement` пишет production code в task scope; `verify` не меняет
production. Общие lifecycle/system-design/archive правила находятся в
`workflow/`, платформенные детали — только в соответствующем корне.

Каждый platform package хранит evidence-selected `engineering_scopes` и точный
derived `applicable_rule_files`. Propose выбирает scopes, Plan может уточнить их
до `planned`, Implement/Verify используют неизменный набор. Flat adapter catalog
не загружается глобально; nontrivial checks выполняются с finite watchdog.

## Инварианты

- Знание хранить в одном каноническом месте; адаптеры должны только связывать
  канон с конкретным runtime.
- Portable skills хранить в `.agents/skills/`; runtime-копии процесса не создавать.
- Не смешивать платформенные правила с общими без необходимости.
- Не коммитить и не публиковать изменения без явной просьбы пользователя.
- Человекочитаемые отчёты и документы писать на русском; код, пути и
  идентификаторы — на английском.

## Commit gate и hooks

Явная просьба о commit сначала запускает portable `$pre-commit-check` по уже
staged index. Gate не выполняет staging, commit, push и не расширяет delivery
authorization. Канон: [`pre-commit-integrity.md`](workflow/rules/pre-commit-integrity.md).

Tracked Git hook находится в [`.githooks/pre-commit`](.githooks/pre-commit), а
runtime hooks делегируют общему
[`hook-runner.py`](workflow/hooks/hook-runner.py). Runtime hook может дать ранний
deny/warning, но обязательной границей остаётся Git hook после явной безопасной
активации `core.hooksPath`; автоматически менять `.git/config` запрещено.
