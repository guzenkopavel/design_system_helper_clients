# Swift concurrency

Isolation является частью design contract. UI state — MainActor. Shared mutable
state — actor или короткая синхронная critical section с rationale. Не применять
`nonisolated`/`@unchecked Sendable` для подавления диагностики. Cancellation и
exit paths явны; task ownership/lifetime определены; I/O под lock запрещён.

CPU parallelism вводить только после evidence; networking уже asynchronous.
Design отмечает crossings, Sendable boundaries, reentrancy и cleanup.
