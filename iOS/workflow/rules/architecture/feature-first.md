# Feature-First

Фича инкапсулирует Data, Domain и Presentation в cohesive physical unit, когда
это подтверждают ownership/consumer signals. Направление зависимостей:
Presentation → Domain contracts ← Data implementations. Domain не импортирует UI
или infrastructure. Между фичами использовать public contracts; shared слой не
содержит feature business logic.

Не создавать пустые слои или module-per-layer ради формы. Placement подтверждать
существующим project/package/target graph; greenfield path маркировать
`proposed`. Новая независимая feature по strong default не реализуется целиком
в application target: app shell только связывает route, DI и lifecycle.

## Boundary checklist

- Feature public API содержит только входы, результаты и route contracts,
  необходимые потребителю.
- Domain models не являются aliases transport/persistence DTO.
- Data adapters реализуют domain-owned contracts и нормализуют внешние ошибки.
- Presentation не импортируется из Domain/Data.
- Общая primitive выносится только после доказанных двух владельцев и
  одинаковой семантики, а не одинакового синтаксиса.
- Cross-feature workflow координируется на composition/navigation boundary.
- Data/repository, networking/transport и storage implementations изолируются
  от feature public API; sources скрыты за domain-owned contracts.

Plan разделяет задачи по observable vertical slices, если это позволяет ранний
RED→GREEN. Массовое создание папок до первого поведения запрещено.
