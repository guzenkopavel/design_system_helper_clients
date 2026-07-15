# Feature-First

Фича инкапсулирует Data, Domain и Presentation. Направление зависимостей:
Presentation → Domain contracts ← Data implementations. Domain не импортирует UI
или infrastructure. Между фичами использовать public contracts; shared слой не
содержит feature business logic.

Не создавать пустые слои ради формы. Placement подтверждать существующим
project/package layout; greenfield path маркировать `proposed`.

## Boundary checklist

- Feature public API содержит только входы, результаты и route contracts,
  необходимые потребителю.
- Domain models не являются aliases transport/persistence DTO.
- Data adapters реализуют domain-owned contracts и нормализуют внешние ошибки.
- Presentation не импортируется из Domain/Data.
- Общая primitive выносится только после доказанных двух владельцев и
  одинаковой семантики, а не одинакового синтаксиса.
- Cross-feature workflow координируется на composition/navigation boundary.

Plan разделяет задачи по observable vertical slices, если это позволяет ранний
RED→GREEN. Массовое создание папок до первого поведения запрещено.
