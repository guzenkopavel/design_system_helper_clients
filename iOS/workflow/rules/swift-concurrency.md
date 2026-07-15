# Swift concurrency

Isolation является частью design contract. UI state — MainActor. Shared mutable
state — actor или короткая синхронная critical section с rationale. Не применять
`nonisolated`/`@unchecked Sendable` для подавления диагностики. Cancellation и
exit paths явны; task ownership/lifetime определены; I/O под lock запрещён.

CPU parallelism вводить только после evidence; networking уже asynchronous.
Design отмечает crossings, Sendable boundaries, reentrancy и cleanup.

## Контракт

- Structured child tasks предпочтительнее unstructured/detached tasks.
- `Task` имеет owner, cancellation trigger и observation path для ошибок.
- После каждого `await` actor-isolated state может измениться; invariants
  перечитываются или валидируются повторно.
- Continuation возобновляется ровно один раз на всех ветвях и не удерживает lock.
- AsyncSequence/subscription завершается при уходе owner.
- Priority не используется как correctness/order mechanism.

Диагностика strict concurrency, default isolation и Sendable зависит от реально
выбранных Swift language mode и compiler settings. Нельзя утверждать поведение
конкретной версии Swift только по установленному Xcode; plan фиксирует найденные
settings и отдельные migration warnings.

`@unchecked Sendable`, `nonisolated(unsafe)` и detached task требуют локального
доказательства thread safety и focused test. Performance benefit параллелизма
измеряется; больше tasks не означает быстрее.
