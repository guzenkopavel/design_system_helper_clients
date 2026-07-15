# Naming

Protocols именуются по capability без `I` и `Protocol`. Основная реализация —
`Default*`, тестовые — `Mock*`/`Stub*`/`Fake*`. Data transport/storage types имеют
`DTO`/`Response`/`Entity`; domain models — business names. Use Case —
`VerbNounUseCase`; Presentation — `FeatureView`, `FeatureViewModel`,
`FeatureState`, `FeatureAction`; navigation — `Coordinator`/`Router`.

Имена следуют существующему codebase, если он имеет устойчивую более точную
convention. Не добавлять suffix только ради слоя. Acronyms оформляются по
настройкам compiler/linter и соседнему коду. Boolean читается как утверждение;
метод с side effect начинается с действия; factory выражает создаваемый тип.

`Manager`, `Helper`, `Util`, `Service` без конкретной ответственности — сигнал
уточнить boundary. Test doubles различаются семантически: stub возвращает
данные, spy записывает interaction, fake реализует упрощённое поведение, mock
проверяет expectation.
