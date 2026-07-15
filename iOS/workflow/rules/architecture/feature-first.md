# Feature-First

Фича инкапсулирует Data, Domain и Presentation. Направление зависимостей:
Presentation → Domain contracts ← Data implementations. Domain не импортирует UI
или infrastructure. Между фичами использовать public contracts; shared слой не
содержит feature business logic.

Не создавать пустые слои ради формы. Placement подтверждать существующим
project/package layout; greenfield path маркировать `proposed`.
