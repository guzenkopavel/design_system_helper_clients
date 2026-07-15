---
phase: discovery
writes_artifacts:
  - specs/product/<feature>/brief.md
requires_verification: focused
inputs:
  - raw idea or chosen concept
outputs:
  - shared product brief
  - draft requirements and acceptance criteria
  - draft screen and flow impact
---

# Phase: Discovery

Discovery превращает идею или выбранный concept в общий для iOS и Android
product brief. Это no-code этап до финальной продуктовой спеки. Граница слоёв —
[`specification-layers.md`](../rules/specification-layers.md).

## Когда применять

- новая фича или значимое изменение наблюдаемого поведения;
- нужно проверить проблему, пользователей, outcomes, scope и предположения;
- выбранное направление есть, но поведенческий контракт ещё не готов.

Чисто техническое изменение одной платформы сюда не направлять. Если
неизвестно само направление, сначала применить `brainstorming`.

## Процедура

1. **Frame:** сформулировать проблему, пользователей, текущее трение, outcome и
   признаки успеха без преждевременного выбора реализации.
2. **Evidence:** отделить факты от допущений; для рискованных допущений указать
   источник или способ проверки. Волатильные внешние ограничения фиксировать,
   не проектируя здесь платформенную архитектуру.
3. **Explore:** использовать существующий concept либо провести сокращённый
   brainstorming с 2–3 вариантами. Зафиксировать выбранное направление и
   отклонённые альтернативы с причинами.
4. **Shape:** описать scope, non-goals, общее observable behavior, основные и
   вторичные состояния: loading, empty, error, offline, accessibility,
   localization, analytics и privacy — только когда применимо.
5. **Draft UX impact:** для UI/interaction scope собрать достаточный вход для
   `ux.md`: user journey и entry/exit points, затронутые или новые surfaces,
   draft screen/flow map, states, navigation, content semantics, interaction
   rules, accessibility/localization, analytics/privacy и ожидаемые роли
   дизайн-системы. Не выбирать SDK, architecture или platform components.
6. **Parity pass:** отдельно проверить ожидаемое поведение iOS и Android.
   Различия SDK или возможностей записать как constraint/open question для
   будущего направления, но не создавать platform design и не менять product
   intent для одной платформы молча.
7. **Draft contract:** создать требования `REQ-N` и observable критерии `AC-N`.
   Каждый AC содержит `Covers: REQ-N`; пробелы разрешены на этой фазе, но явно
   помечаются как draft gaps.
8. Записать `specs/product/<feature>/brief.md` по
   [`product-brief.md`](../templates/product-brief.md) и передать в `elaborate`.

## Gate

Brief готов к передаче, когда выбранное направление обосновано, scope и
non-goals явны, допущения видимы, оба клиента рассмотрены, а вопросы реализации
не выданы за продуктовые решения. Для UI/interaction scope draft screen/flow
impact и secondary concerns достаточно полны, чтобы UX-решения не откладывались
в платформенный downstream.
