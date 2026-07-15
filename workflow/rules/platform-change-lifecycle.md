# Platform change lifecycle

## Package

Пакет одного направления живёт в `<platform>/specs/<feature>/` и содержит:

- `meta.json` — machine-readable lifecycle;
- `proposal.md` — platform goal, intake, scope, decisions и open questions;
- `implementation-spec.md` — только platform requirements/AC и ссылки на shared IDs;
- `design.md` — architecture, SDK, module boundaries, data/control flow;
- `verification.md` — traceability к доказательствам;
- после plan — `plan/README.md` и `plan/task-NNN.md`.

Конкретные platform name/root/prefix/guard/design gates поставляет единственный
`<platform>/workflow/platform-contract.json`. Common validator обнаруживает
adapter, но не содержит platform IDs или SDK rules.

Минимальные поля `meta.json`: `platform`, `feature`, `change_type`, `tier`,
`status`, `shared_product_spec`, `product_status`, `product_approval`,
`product_impact`, `impact_evidence`, `blocking_questions`, `design_gate`,
`tasks_total`. Допустимые статусы: `draft`, `specified`, `planned`.
`design_gate` принимает `pending` или `PASS`. Validator вычисляет PASS по
содержимому `design.md`, а не доверяет полю. Для Quick допустим
`Design status: NOT_APPLICABLE: <reason>` внутри design, но успешный transition
всё равно фиксируется как `design_gate: PASS` после проверки причины.

## Transitions

```text
no package → propose → specified → plan → planned
```

- `specified` требует валидного intake, всех propose-артефактов, закрытых
  blockers, REQ↔AC coverage и tier design gate.
- `planned` требует `specified`, непрерывных task IDs и `tasks_total > 0`.
- validator — fail-closed; невалидный пакет не повышает status.

## Tier

- `quick`: локальный низкорисковый change; design может быть `N/A` с причиной.
- `standard`: обычная feature/change; design обязателен.
- `extended`: новый модуль, миграция, cross-boundary, security/privacy,
  concurrency или hard-to-reverse dependency; применяются все system-design и
  gates выбранного platform adapter.

## Contract separation

Shared `REQ-*`/`AC-*` остаются только в `specs/product/<feature>/spec.md`.
Для product-backed `shared_product_spec` равен этому пути буквально для того же
strict kebab-case feature slug; absolute paths, `..` и ссылка на другую фичу
невалидны.
Платформенная спека перечисляет их IDs и mapping, не переписывает observable
формулировки. Собственные технические контракты используют
`<PLATFORM_PREFIX>-REQ-N` и `<PLATFORM_PREFIX>-AC-N`; каждый platform AC
содержит `Covers:` хотя бы одного объявленного platform requirement.

Platform constraint, меняющий product behavior, блокирует package и возвращает
решение в shared product layer.
