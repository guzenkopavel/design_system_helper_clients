# SwiftUI rendering performance

Применяется только если найден SwiftUI surface. Сначала измерить body updates,
layout/drawing cost, identity churn и data flow.

- State хранится у минимального owner; широкие observable dependencies не
  заставляют нерелевантное subtree обновляться.
- Collection identity стабильна и соответствует domain identity.
- Тяжёлая работа не выполняется в `body`; derived data кешируется только с
  корректной invalidation policy.
- Equatable/custom diff optimizations добавляются после trace, не заранее.
- Image loading/decode/cancellation связано с view lifecycle без duplicate work.
- Animations/transitions проверяются на correctness, Reduce Motion и frame cost.

Количество `body` evaluations само по себе не bug; важен measured user-visible
cost. SDK rendering behavior и доступные diagnostics подтверждаются текущим
toolchain/deployment target.
