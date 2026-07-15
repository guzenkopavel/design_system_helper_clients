# Type design

Тип имеет одну причину изменения, cohesive state и минимальный public surface.
Default — value type; class требует identity/lifecycle/inheritance rationale.
Dependencies направлены на contracts. Extension группирует одну тему; повторный
type switch — сигнал вынести variation за protocol/factory. Размер типа — review
signal, не механическая цель.

Enums моделируют конечные состояния и несут associated data вместо нескольких
несогласованных optionals. Raw strings/integers оборачиваются, когда имеют
domain invariants или разные единицы. Public initializer не допускает invalid
state; throwing/failable construction используется только когда invalid input
реально приходит с boundary.

Protocol создаётся от потребителя и остаётся узким. Не вводить protocol для
каждого concrete type ради «testability», если value type можно передать прямо.
Generic abstraction оправдана повторяющимся контрактом и понятной диагностикой.
Reference semantics требует identity, shared ownership или framework lifecycle;
иначе default — value semantics.
