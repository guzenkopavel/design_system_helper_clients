# Use Cases

Use Case — одна бизнес-операция с явными input/output, domain errors и
dependencies только на Domain contracts. В нём нет UI, navigation, DTO/storage
types или thread switching. Idempotency/retry/order/cache semantics фиксируются,
если применимы.

Checklist для plan task: одна ответственность; явный contract; domain models и
errors; validation/business rules внутри; no main-thread promise; deterministic
tests всех branches; composition без скрытого infrastructure.
