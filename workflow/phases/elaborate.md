---
phase: elaborate
writes_artifacts:
  - specs/product/<feature>/brief.md
  - specs/product/<feature>/ux.md (UI/interaction only)
  - specs/product/<feature>/spec.md
  - specs/product/<feature>/review-verdicts.json
requires_verification: focused
recommended_roles:
  - product-spec-reviewer
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

1. Если существует `specs/product/<feature>/SPECIFICATION.md`, прочитать его как
   immutable current baseline. Candidate `spec.md` обязан быть полным
   post-change контрактом и явно сохранять либо осознанно менять его behavior.
   Baseline не редактировать и не включать в review fingerprint.
2. Если направление не выбрано, выполнить
   [`brainstorming`](brainstorming.md).
3. Если нет качественного brief, выполнить [`discovery`](discovery.md).
4. Для UI/interaction scope сформировать или обновить
   `specs/product/<feature>/ux.md` по
   [`product-ux.md`](../templates/product-ux.md) и общему
   [`visual-language.md`](../rules/visual-language.md): soft blue выражать
   semantic roles без platform APIs. Для non-UI scope явно
   зафиксировать `UX artifact: NOT APPLICABLE` с причиной.
5. Сформировать или обновить `specs/product/<feature>/spec.md` по
   [`product-spec.md`](../templates/product-spec.md).
6. Через [`validate-product-spec.py`](../scripts/validate-product-spec.py)
   получить candidate fingerprint. Провести isolated review/fix cycles по
   [`product-spec-review.md`](../rules/product-spec-review.md); intermediate
   outputs не являются durable receipt.
7. Представить пакет человеку для явного product approval. До явного решения
   сохранить `Product approval: PENDING`; approval не выводить из молчания или
   предыдущего обсуждения. При одобрении записать approver и evidence решения.
8. Approval меняет fingerprint. После закрытия всех blockers до snapshot
   выставить exact `Readiness Decision: READY/none`, сохраняя metadata Status
   `DRAFT` до green receipt; повторно выполнить `snapshot`, затем ровно шесть
   финальных вызовов `product-spec-reviewer`, каждый в отдельном fresh context,
   с одним lens и тем же fingerprint. Не передавать writer rationale или другие
   lens outputs. Coordinator фиксирует один parent review session и для каждого
   вызова сохраняет runtime-issued invocation evidence; JSON только attests эти
   identities и сам по себе не доказывает isolation. Product и cross-client
   parity всегда REQUIRED.
9. Coordinator валидирует outputs и выполняет `aggregate --write`; reviewer не
   пишет `review-verdicts.json`. Exact six valid GAP/UNKNOWN сохраняются в
   durable non-green receipt; missing/mixed/duplicate/invalid не создают receipt.
   Любой non-PASS или unavailable independent context сохраняет DRAFT.
10. После green receipt изменить только exact `Status: DRAFT` на `READY`, затем запустить
   финальный `validate-product-spec.py check`. Только его PASS
   разрешает fan-out.

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
  `Covers:` на существующее требование, описывает ровно один наблюдаемый
  результат и задаёт уникальную `Verification dimension`;
- appearance/accessibility dimensions атомарны: assistive semantics, text
  scaling, light/dark, increased contrast и иные независимо наблюдаемые
  outcomes не склеены в один AC;
- для iOS и Android отдельно рассмотрены happy path и применимые loading,
  empty, error, offline, accessibility, localization, analytics/privacy states;
- платформенные ограничения не превратились в скрытый fork product intent;
- для UI/interaction scope существует полный `ux.md`, его screen/flow impact,
  states, semantics и shared design-system intent согласованы со spec;
- свежий `review-verdicts.json` содержит exact шесть isolated lens outputs на
  одном текущем fingerprint и parent review session; applicable verdicts PASS,
  а N/A обоснованы; provenance attestation ссылается на runtime audit evidence;
- `Product approval: APPROVED`, указан approver и evidence явного human
  решения;
- нет блокирующих open questions;
- Client Readiness показывает полноту shared contract для iOS и Android, а не
  готовность downstream implementation; все terminal rows exact PASS;
- Readiness Decision exact `READY/none` и не противоречит metadata, Client
  Readiness или Open Questions.

Если хотя бы один пункт не выполнен, статус остаётся `DRAFT`. В частности, без
явного human approval результат обязан быть `DRAFT / PENDING APPROVAL`, даже
если требования и review уже полны.
Same-context/no-subagent fallback всегда `independent_context: false`, verdict
`UNKNOWN` и DRAFT; его нельзя называть independent PASS.

## Stop boundary

После `READY` остановиться. Не создавать platform package в
`<platform>/specs/<feature>/changes/<change-id>/`, не запускать реализацию и не
писать production code.
Следующий отдельный workflow создаёт implementation spec нужного направления
по [`platform-implementation-spec.md`](../templates/platform-implementation-spec.md)
и ссылается на общий продуктовый контракт.

Ясная product-мелочь может начать сразу с этого driver. Чисто техническое
изменение без изменения observable behavior должно обойти `elaborate`.
