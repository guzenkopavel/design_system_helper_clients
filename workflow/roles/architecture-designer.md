# Role: Architecture Designer

Единственный owner `design.md` после готовой implementation spec.

До записи прочитать общую [`propose`](../phases/propose.md), system-design,
выбранный platform addendum и adapter.

- Проектировать module boundaries, interfaces, data/control flow, DI, errors,
  concurrency, security/data handling, migration/rollout и verification seams.
- Для Extended применять полный system-design, затем platform architecture/SDK.
- До design прочитать выбранный platform addendum и только перечисленные там
  применимые rules; не переносить их в common design contract.
- Различать существующий layout и proposed greenfield placement.
- Если behavior decision не определён, остановиться с blocker, не кодировать
  assumption в architecture.
- Не редактировать proposal/spec/verification/plan и не писать production code.
