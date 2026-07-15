# Design gates

Для каждого applicable риска design фиксирует решение, альтернативы и проверку.

- Third-party: maintenance, license, security, binary size, API stability,
  минимум две альтернативы, boundary wrapper.
- Security/privacy: threat-first controls, secrets, data minimization, logging,
  transport и deletion policy.
- Persistence migration: versioning, N-2 compatibility where required, realistic
  data test, failure/rollback path.
- State machine: таблица stage × success/error/timeout/cancel/nil exit + cleanup.
- Router/mapper/planner/dispatcher: input → output decision table.
- Domain mapping: каждое source field mapped либо discarded с rationale.
- External decisions: typed contract fields; string heuristics запрещены.
- Correlation IDs: self/reference semantics и реальный источник каждого ID.

Platform-specific SDK gates добавляются platform phase, не копируются сюда.
