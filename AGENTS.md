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

## Инварианты

- Знание хранить в одном каноническом месте; адаптеры должны только связывать
  канон с конкретным runtime.
- Portable skills хранить в `.agents/skills/`; runtime-копии процесса не создавать.
- Не смешивать платформенные правила с общими без необходимости.
- Не коммитить и не публиковать изменения без явной просьбы пользователя.
- Человекочитаемые отчёты и документы писать на русском; код, пути и
  идентификаторы — на английском.
