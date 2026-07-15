---
phase: propose
writes_artifacts:
  - <platform>/specs/<feature>/meta.json
  - <platform>/specs/<feature>/proposal.md
  - <platform>/specs/<feature>/implementation-spec.md
  - <platform>/specs/<feature>/design.md
  - <platform>/specs/<feature>/verification.md
requires_verification: focused
recommended_roles:
  - repo-navigator
  - specification-writer
  - architecture-designer
---

# Phase: Propose

Преобразовать утверждённый shared product contract или доказанный technical-only
intake в implementation package **одной платформы**. Production code не писать.

## Intake

Форма: `propose <platform> <feature> [--tier quick|standard|extended] [--technical-only]`.

- platform и feature обязательны;
- platform runtime обязан выбрать ровно один зарегистрированный adapter;
- missing/unknown/unavailable adapter блокирует phase до любых записей;
- default tier — `standard`; повышение tier допустимо, понижение после записи
  design decisions — только с явным обоснованием.

`product-backed` требует `specs/product/<feature>/spec.md` со статусом `READY`,
`Product approval: APPROVED` и approval evidence. Платформенный пакет ссылается
на shared `REQ-*`/`AC-*`, но не копирует их текст.

`--technical-only` требует записанного `Product impact assessment: NONE` и
evidence неизменности observable behavior. `PRESENT`/`UNCERTAIN` блокирует
phase и возвращает работу в product elaboration.

## Workflow

1. Запустить context retrieval и получить verified existing paths, proposed
   greenfield paths, integration points и excluded noise.
2. Зафиксировать tier, change type, scope/non-goals, decisions, open questions и
   фактические code zones.
3. Роль `specification-writer` единолично пишет `proposal.md`,
   `implementation-spec.md`, `verification.md`. Платформенные требования имеют
   ID `<PLATFORM_PREFIX>-REQ-N`, AC — `<PLATFORM_PREFIX>-AC-N` с `Covers:`;
   prefix поставляет adapter.
4. Роль `architecture-designer` единолично пишет `design.md`, если tier требует
   design. Выбранный platform boundary guard только проверяет placement.
5. Quick: design может быть `N/A` только с bounded rationale. Standard: design
   обязателен. Extended: пройти полный system-design и platform design gates.
6. Verification трассирует каждый shared/platform requirement и AC к review,
   unit/UI/integration/build evidence. Platform addendum добавляет обязательные
   runtime surfaces.
7. Выполнить `workflow/scripts/workflow-reflection.py propose`, закрыть blocking
   questions, записать candidate `status: specified` и прогнать validator. При
   ошибке вернуть `draft`; только green сохраняет transition.

Перед validator применить [`wording-clarity`](../rules/wording-clarity.md).

## Ownership

`specification-writer` не редактирует `design.md`; `architecture-designer` не
редактирует proposal/spec/verification. Ни одна роль не пишет одновременно с
другой. Meta обновляет coordinator после валидного результата.

Общий lifecycle: [`platform-change-lifecycle.md`](../rules/platform-change-lifecycle.md).
Платформенное addendum выбирается после нормализации platform.
