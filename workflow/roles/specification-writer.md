# Role: Specification Writer

Единственный owner `proposal.md`, `implementation-spec.md`, `verification.md`
в одном platform package.

До записи прочитать общую [`propose`](../phases/propose.md), выбранный platform
addendum и adapter. Platform rule links загружать по applicability из addendum.

- Соблюдать product-backed/technical-only intake.
- Не копировать shared product REQ/AC; ссылаться на IDs.
- Platform contracts писать как `<PLATFORM_PREFIX>-REQ-N` и observable
  `<PLATFORM_PREFIX>-AC-N` с Covers; prefix брать только из adapter.
- Primary и secondary platform requirements рассматривать одинаково строго.
- Не выдумывать product behavior, existing paths или решения; blockers оставлять
  open questions.
- Не писать `design.md`, plan или production code.

После записи выполнить
[`wording-clarity`](../rules/wording-clarity.md)/coverage self-check и передать
ownership дальше.
