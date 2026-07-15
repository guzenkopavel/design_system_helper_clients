# Type design

Тип имеет одну причину изменения, cohesive state и минимальный public surface.
Default — value type; class требует identity/lifecycle/inheritance rationale.
Dependencies направлены на contracts. Extension группирует одну тему; повторный
type switch — сигнал вынести variation за protocol/factory. Размер типа — review
signal, не механическая цель.
