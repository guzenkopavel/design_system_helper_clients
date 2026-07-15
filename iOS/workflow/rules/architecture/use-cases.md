# Use Cases

Use Case — одна бизнес-операция с явными input/output, domain errors и
dependencies только на Domain contracts. В нём нет UI, navigation, DTO/storage
types или thread switching. Idempotency/retry/order/cache semantics фиксируются,
если применимы.

Checklist для plan task: одна ответственность; явный contract; domain models и
errors; validation/business rules внутри; no main-thread promise; deterministic
tests всех branches; composition без скрытого infrastructure.

Input может быть value type, когда параметров несколько или важны invariants.
Output различает отсутствие данных, бизнес-отказ и infrastructure failure.
Use Case не выбирает экран, локализованный текст или transport retry без
domain-policy.

Async contract фиксирует cancellation propagation и допустимость повторного
вызова. Если операция изменяет состояние, design отвечает на вопросы
idempotency, ordering и partial success. Оркестрация нескольких dependencies
остаётся последовательной, пока независимость и benefit параллелизма не
доказаны измерением.
