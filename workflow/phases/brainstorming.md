---
phase: brainstorming
writes_artifacts:
  - specs/product/<feature>/concept.md (optional)
requires_verification: smoke
inputs:
  - raw idea or problem
outputs:
  - brainstorm frame
  - 2-3 alternatives and recommendation
  - optional specs/product/<feature>/concept.md
---

# Phase: Brainstorming

Pre-spec, no-code фаза для сырой идеи, когда проблема, scope или направление
ещё не ясны. Каноническая граница артефактов описана в
[`specification-layers.md`](../rules/specification-layers.md).

## Когда применять

- есть реальная развилка или существенные trade-offs;
- пользователь просит исследовать идею до формализации;
- принятое решение кажется основанным на привычке, а не на ограничениях.

Для ясной продуктовой задачи перейти к `discovery`. Для чисто технического
изменения одной платформы product elaboration не запускать.

## Процедура

1. Собрать `Brainstorm Frame`: Problem, Goal, Current Context, Known
   Constraints, Unknowns и Decision Needed.
2. Разделить реальные ограничения и принятые допущения. Для рискованных
   допущений указать, какое evidence их подтвердит или опровергнет.
3. Сформировать 2–3 реалистичных варианта только при настоящих trade-offs. Для
   каждого описать shape, затронутое пользовательское поведение, плюсы, цену,
   риски и условия успеха.
4. Выбрать рекомендуемое направление и объяснить решение через goal,
   ограничения и риски. Не скрывать противоречия ради удобного ответа.
5. Зафиксировать open questions и следующий вход: `discovery`, `elaborate` или
   платформенная работа для чисто технического изменения.

## Persistence

По умолчанию результат остаётся в ответе. Создавать
`specs/product/<feature>/concept.md` по
[`product-concept.md`](../templates/product-concept.md) только по явной просьбе
или при согласованном переходе в discovery. Concept общий для iOS и Android;
платформенные implementation specs эта фаза не создаёт.

## Формат результата

1. Brainstorm Frame
2. Options
3. Recommended Direction
4. Open Questions
5. Next Workflow
