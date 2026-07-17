# Инспекция current code после recovery

## Статус

`PASS`

## Наблюдения

- `Android/settings.gradle.kts` включает отдельный модуль `:my-profile`.
- `Android/app/build.gradle.kts` зависит от публичного контракта
  `project(":my-profile")`.
- `Android/my-profile` владеет repository, remote data source, состоянием
  route, `Compose` экраном, ресурсами профиля и проверками.
- `Android/app-shell` предоставляет только `profileContent` slot и не владеет
  данными, repository или сетевой логикой профиля.
- `Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt` создаёт
  зависимости и передаёт callback очистки сессии; состояние профиля,
  восстановление и logout flow принадлежат `ProfileRoute` в модуле
  `:my-profile`.
- Восстановимые пользовательские строки профиля принадлежат ресурсам
  профильного модуля, а не hardcoded строкам application module.
- `DefaultProfileRemoteDataSource` не превращает `CancellationException` в
  offline failure.
