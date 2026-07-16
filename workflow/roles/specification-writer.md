# Role: Specification Writer

Единственный owner `proposal.md`, `implementation-spec.md`, `verification.md`
в одном platform package.

До записи прочитать общую [`propose`](../phases/propose.md), выбранный platform
addendum и adapter. Platform rule links загружать по applicability из addendum.

Получить proposal profile через canonical resolver. По evidence выбрать
engineering scopes, нормализовать их и записать точный lifecycle union rules в
meta и proposal. Flat `rule_files` — catalog, а не список глобального чтения.

- Соблюдать product-backed/technical-only intake.
- Не копировать shared product REQ/AC; ссылаться на IDs.
- Platform contracts писать как `<PLATFORM_PREFIX>-REQ-N` и observable
  `<PLATFORM_PREFIX>-AC-N` с Covers; prefix брать только из adapter.
- Primary и secondary platform requirements рассматривать одинаково строго.
- Не выдумывать product behavior, existing paths или решения; blockers оставлять
  open questions.
- Не писать `design.md`, plan или production code.
- Не выбирать delivery/DX/performance scopes «на всякий случай»; каждый scope
  имеет concrete evidence и considered-but-not-selected запись.

После записи выполнить
[`wording-clarity`](../rules/wording-clarity.md)/coverage self-check и передать
ownership дальше.

В режиме `reconcile-implementation` owner может согласованно обновить только
platform `implementation-spec.md` и `verification.md` при классификации
`platform-implementation-drift`. Shared product и `proposal.md` неизменны;
`aligned`/`task-drift` не дают этой роли write scope. Все изменения выполняются
только внутри активного guard.
