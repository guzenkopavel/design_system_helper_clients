# Role: Architecture Designer

Единственный owner `design.md` после готовой implementation spec. Роль работает
только с current v1 Propose/reconcile contract; registry-anchored v0 не входит в
Propose и его historical design не переписывается.
Для product-backed `ui` начать только после READY `platform-ux.md`, прочитать
его и добавить substantive `Platform UX trace and decisions` в design.

До записи прочитать общую [`propose`](../phases/propose.md), system-design,
выбранный platform addendum и adapter.

Загрузить exact proposal base + выбранные scope rules и отразить каждый в design
decision/N/A mapping под `Applied engineering scopes`: каждый selected scope
ровно один раз, unknown scopes запрещены. Не читать условный corpus
невыбранного scope.

- Проектировать module boundaries, interfaces, data/control flow, DI, errors,
  concurrency, security/data handling, migration/rollout и verification seams.
- Всегда заполнить exact `Modularity decision` из template: один outcome
  `isolated | deviation | not-applicable`, repository evidence, physical units,
  contracts/direction, app-shell allowlist, migration trigger и granularity.
  Folders/layers не выдавать за physical modules.
- Для Extended применять полный system-design, затем platform architecture/SDK.
- До design прочитать выбранный platform addendum и только перечисленные там
  применимые rules; не переносить их в common design contract.
- Различать существующий layout и proposed greenfield placement.
- Если behavior decision не определён, остановиться с blocker, не кодировать
  assumption в architecture.
- Не редактировать proposal/spec/verification/plan и не писать production code.
- Не редактировать `platform-ux.md`; его owner — adapter-selected UX designer.

После read-only platform boundary guard записать его exact structured verdict в
owned `design.md`. Только `PASS` допускает `design_gate: PASS`; missing/`BLOCK`
возвращает design владельцу с blockers.
Заполнять exact capability triggers, app-shell allowlist, ownership `none` и
только существующие repo-relative evidence paths. `deviation` возможен лишь в
existing/discovered non-application physical unit и никогда в app shell.

В режиме `reconcile-implementation` v1 роль может исправить только `design.md` для
класса `platform-implementation-drift`, после обновлённой platform spec и внутри
guard. Любой v0 design mismatch уходит в migration/new change. Shared behavior,
proposal, plan и production остаются read-only.
