# Инспекция current code для verify

## Статус

`FAIL`

## Наблюдения

- `Android/settings.gradle.kts` включает `:my-profile`, а
  `Android/app/build.gradle.kts` зависит от `project(":my-profile")`.
- `Android/my-profile` содержит repository, remote data source, UI state,
  Compose screen, strings и tests профильной capability.
- `Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShell.kt`
  предоставляет `profileContent` slot и не владеет profile data/network logic.
- `Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt` содержит
  `ProfileDestinationContent`, создаёт `DefaultProfileRepository`, владеет
  `ProfileUiState`, мапит `ProfileLoadResult`, управляет logout state и
  invalid-session recovery. Это нарушает boundary, где `:app` должен оставаться
  entry/root composition/wiring, а profile capability должна владеть состоянием
  и policy.
- `MainActivity.kt` содержит hardcoded user-facing recovery string
  `"Нет сетевого подключения"` вне resources профильного модуля.
- `DefaultProfileRemoteDataSource.execute()` ловит общий `Exception` и
  превращает его в `ProfileFailure.Offline`, что не доказывает propagation
  cancellation для real OkHttp source.
