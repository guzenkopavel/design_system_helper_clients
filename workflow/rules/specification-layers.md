# Specification layers

Продуктовая проработка и платформенное проектирование — разные слои с разными
владельцами. Граница обязательна для любой функциональности, общей для
мобильных клиентов.

## Shared product layer

Единый источник продуктовой истины для iOS и Android находится в
`specs/product/<feature>/`:

- `concept.md` — опциональная фиксация результата brainstorming;
- `brief.md` — результат discovery: проблема, доказательства, выбранное
  направление, scope и черновой поведенческий контракт;
- `ux.md` — обязательная для UI/interaction-фич общая UX-проработка: journey,
  flow, screen impact, states/navigation/content, interaction semantics и
  design-system intent без платформенной реализации;
- `spec.md` — итоговый продуктовый контракт со статусом `DRAFT` или `READY`.

Этот слой отвечает на вопросы «зачем» и «что наблюдает пользователь». Он един
для обоих клиентов и не содержит имён классов, модулей, SDK, фреймворков,
архитектурных паттернов или планов миграции.

До платформенного fan-out в продуктовый пакет должны попасть:

- проблема, целевые пользователи, outcomes и признаки успеха;
- scope, non-goals, выбранный вариант и продуктовые решения;
- общее наблюдаемое поведение и состояния для iOS и Android;
- требования `REQ-N` и критерии `AC-N`, где каждый AC содержит `Covers:` со
  ссылкой минимум на одно требование, а каждое требование покрыто AC;
- общие продуктовые ограничения, допущения, evidence и open questions.

Для UI/interaction-фич `ux.md` дополнительно фиксирует accessibility,
localization, analytics/privacy, роли компонентов дизайн-системы,
token/semantic intent и допустимую платформенную вариативность. Он не содержит
SDK, архитектуру клиента или выбор конкретных implementation-компонентов.

До `READY` пакет проходит применимые review lenses:

- product;
- UX/accessibility для UI и interaction scope;
- design-system для UI scope;
- data/analytics/privacy, если затронуты данные или измерения;
- security, если затронуты авторизация, чувствительные данные или abuse cases;
- cross-client parity — всегда.

Для каждой линзы фиксируются applicability, verdict и findings/gaps.

`spec.md` получает статус `READY`, только если нет блокирующих open questions,
поведение проверено отдельно для iOS и Android, матрица REQ↔AC полна,
применимый `ux.md` прошёл review и человек явно одобрил продуктовый пакет.
Approval нельзя выводить из отсутствия возражений: `spec.md` хранит
`Product approval: APPROVED`, approver и evidence явного решения. Без этого статус —
`DRAFT`, а approval — `PENDING`.

## Platform implementation layer

Платформенный intake имеет ровно два допустимых режима:

1. **`product-backed`** — изменение реализует или меняет observable product
   behavior. Обязательна ссылка на `specs/product/<feature>/spec.md` со
   статусами `READY` и `Product approval: APPROVED`.
2. **`technical-only`** — изменение допускается без shared product spec только
   при явном `Product impact assessment: NONE` и evidence, что observable
   behavior, product requirements и acceptance criteria не меняются. Например,
   это может быть обновление build tooling или инфраструктуры направления.

`technical-only` нельзя использовать как обход product gates. Если impact
обнаружен, не доказан или остаётся `UNCERTAIN`, работу необходимо вернуть в
product elaboration и продолжить как `product-backed`.

После допустимого intake работа размещается по направлениям:

- `iOS/specs/<feature>/changes/<change-id>/` — active iOS change package;
- `Android/specs/<feature>/changes/<change-id>/` — active Android package for
  propose/plan/implement capabilities.

`change_id` отделяет последовательные или параллельные implementation cycles
одной feature. Product SSOT identity остаётся feature-level. Platform archive
не меняет shared source, а product archive не переписывает platform packages.

В режиме `product-backed` платформенная спека обязана ссылаться на shared spec
и не может копировать, ослаблять или переопределять продуктовые требования и
AC. В обоих режимах в ней остаются архитектура и design реализации,
SDK/framework/module details, реальные платформенные ограничения, применимая
трассировка к тестам, план реализации, миграции и rollout.

Engineering corpus выбирается отдельно от product behavior: package хранит
evidence-selected scopes и exact applicable lifecycle rules. Это не копирует
правила в spec, а делает architecture/testing/performance context аудируемым и
стабильным между Propose, Plan, Implement и Verify.

Если ограничение одной платформы конфликтует с общим контрактом, оно не
превращается молча в отдельное продуктовое поведение. Конфликт возвращается в
product layer как open question или явное продуктовое решение.

## Routing

```text
raw idea
  → brainstorming (optional)
  → discovery
  → elaborate (shared UX when applicable + reviews + human approval)
  → specs/product/<feature>/spec.md: READY
  → <platform>/specs/<feature>/changes/<change-id>/
```

```text
technical platform change
  → product impact assessment: NONE + evidence
  → <platform>/specs/<feature>/changes/<change-id>/ (technical-only)
```

- Ясная продуктовая мелочь может пропустить brainstorming и начать с discovery
  либо сразу с elaborate, если brief уже дан пользователем.
- Чисто техническое изменение одной платформы, не меняющее наблюдаемое
  поведение, обходит product elaboration и сразу идёт в платформенную
  specification/planning фазу.
- Ни одна из трёх product-elaboration фаз не пишет production code.
