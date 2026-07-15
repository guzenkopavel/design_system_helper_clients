# Naming

Protocols именуются по capability без `I` и `Protocol`. Основная реализация —
`Default*`, тестовые — `Mock*`/`Stub*`/`Fake*`. Data transport/storage types имеют
`DTO`/`Response`/`Entity`; domain models — business names. Use Case —
`VerbNounUseCase`; Presentation — `FeatureView`, `FeatureViewModel`,
`FeatureState`, `FeatureAction`; navigation — `Coordinator`/`Router`.
