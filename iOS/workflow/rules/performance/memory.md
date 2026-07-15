# Memory performance

Сначала определить symptom: growth, peak, leak, churn или retained graph.
Сравнивать одинаковый lifecycle scenario и build configuration.

- Проверить closure/delegate/task/subscription ownership и teardown.
- Кеш имеет cost model, bounded capacity и eviction/invalidation policy.
- Большие images/data декодируются/обрабатываются с учётом peak copies.
- Autorelease behavior исследуется инструментом; случайный autoreleasepool не
  является универсальным fix.
- Background/scene transitions освобождают ресурсы согласно owner contract.
- Leak detector/snapshot подтверждается object graph или allocation evidence.

Снижение памяти не должно ломать cache correctness или повторно загружать сеть
без budget. Verify фиксирует baseline/after distributions и residual retained
owners.
