---
phase: elaborate
writes_artifacts:
  - specs/product/<feature>/brief.md
  - specs/product/<feature>/ux.md (UI/interaction only)
  - specs/product/<feature>/spec.md
requires_verification: focused
inputs:
  - product idea, concept, or brief
outputs:
  - DRAFT or human-approved READY shared product specification
---

# Phase: Elaborate

Ручной end-to-end driver всей продуктовой проработки. Он доводит общий пакет
до `READY` и останавливается перед платформенным fan-out. Каноническая граница —
[`specification-layers.md`](../rules/specification-layers.md).

## Routing

1. Если направление не выбрано, выполнить
   [`brainstorming`](brainstorming.md).
2. Если нет качественного brief, выполнить [`discovery`](discovery.md).
3. Для UI/interaction scope сформировать или обновить
   `specs/product/<feature>/ux.md` по
   [`product-ux.md`](../templates/product-ux.md). Для non-UI scope явно
   зафиксировать `UX artifact: NOT APPLICABLE` с причиной.
4. Сформировать или обновить `specs/product/<feature>/spec.md` по
   [`product-spec.md`](../templates/product-spec.md).
5. Провести applicable review lenses и записать verdict/findings/gaps в spec:
   product; UX/accessibility; design-system; data/analytics/privacy; security;
   cross-client parity. Для `N/A` обязательна причина.
6. Представить пакет человеку для явного product approval. До явного решения
   сохранить `Product approval: PENDING`; approval не выводить из молчания или
   предыдущего обсуждения. При одобрении записать approver и evidence решения.
7. Провести readiness review и либо поставить `Status: READY`, либо вернуть
   `Status: DRAFT` со списком gaps.

## Содержание итогового пакета

Перенести в product layer всё, что должно быть согласовано до платформенного
проектирования: problem/why, outcomes/success, scope/non-goals, выбранный
вариант и продуктовые решения, общий observable behavior, требования, AC,
общие constraints и open questions. Для UI/interaction-фич сюда входит общий
UX и design-system intent из `ux.md`, но не платформенная реализация.

Не включать архитектуру клиента, имена SDK/framework/module, platform design,
тестовые классы, implementation/migration/rollout plan. Это downstream scope
будущих platform implementation specs.

## Readiness review

Перед `READY` проверить:

- проблема, outcome, success signals, scope и non-goals непротиворечивы;
- выбранные продуктовые решения и отклонённые альтернативы прослеживаются;
- каждое `REQ-N` покрыто минимум одним `AC-N`, каждый AC ссылается через
  `Covers:` на существующее требование и описывает наблюдаемый результат;
- для iOS и Android отдельно рассмотрены happy path и применимые loading,
  empty, error, offline, accessibility, localization, analytics/privacy states;
- платформенные ограничения не превратились в скрытый fork product intent;
- для UI/interaction scope существует полный `ux.md`, его screen/flow impact,
  states, semantics и shared design-system intent согласованы со spec;
- все applicable review lenses имеют `PASS`, gaps закрыты, а `N/A` обоснованы;
- `Product approval: APPROVED`, указан approver и evidence явного human
  решения;
- нет блокирующих open questions.

Если хотя бы один пункт не выполнен, статус остаётся `DRAFT`. В частности, без
явного human approval результат обязан быть `DRAFT / PENDING APPROVAL`, даже
если требования и review уже полны.

## Stop boundary

После `READY` остановиться. Не создавать `iOS/specs/<feature>/` или
`Android/specs/<feature>/`, не запускать реализацию и не писать production code.
Следующий отдельный workflow создаёт implementation spec нужного направления
по [`platform-implementation-spec.md`](../templates/platform-implementation-spec.md)
и ссылается на общий продуктовый контракт.

Ясная product-мелочь может начать сразу с этого driver. Чисто техническое
изменение без изменения observable behavior должно обойти `elaborate`.
