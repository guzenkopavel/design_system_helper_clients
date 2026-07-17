# Plan — user-profile-auth / iOS / user-profile-auth-public-contract-repair

## Planning frame

Этот план является замещающим ремонтом после явного retirement старого
незавершённого пакета `user-profile-auth`. Он не создаёт новое общее поведение
и не расширяет продуктовый контракт: задача доводит уже начатую реализацию
`AuthFeature` до утверждённого iOS-дизайна, где публичная поверхность пакета
минимальна, флоу авторизации закрывается через `AuthSessionModel`, а внутренние
варианты использования, клиент, хранилище и модель представления остаются за
границей `internal`.

Зафиксированные области остаются полным пересечением затронутого ремонта:
`application`, `concurrency`, `networking`, `package`, `ui`. Они нужны потому,
что публичный контракт пакета, фабричная композиция, асинхронный сессионный
флоу, сетевые и storage-абстракции, а также SwiftUI-флоу должны быть проверены
одним согласованным изменением, а не набором независимых косметических правок.

## DAG

```
task-001 → task-002 → task-003
```

- task-001: приведение публичного контракта `AuthFeature` к дизайну и связывание
  успешного флоу с моделью сессии.
- task-002: интеграция `AuthFeature` в корневую композицию приложения и
  подключение локального пакета к проекту.
- task-003: сквозные UI-тесты входа, регистрации, ветвления и перехода в
  оболочку на детерминированной заглушке.

## Estimates and multipliers

Оценка задачи: 1–2 идеальных дня, потому что ремонт охватывает публичную
API-поверхность, внутреннюю композицию, состояние представления и
сфокусированные модульные тесты. Риск выше обычной косметической правки:
изменение видимости типов должно одновременно сохранить сборку пакета, тестовую
доступность через `@testable` и будущую интеграцию корневой композиции.

Команды проверки:

- Тесты пакета: `xcodebuild test -scheme AuthFeature-Package -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5'`
- Сборка приложения: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build`
- UI-тесты приложения: `xcodebuild test -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:SysDevScenUITests`
- Ограничитель выполнения: `workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 90 --max-output-lines 6000 -- xcodebuild test -scheme AuthFeature-Package`
- Статическая проверка публичного контракта: `rg -n "public |open " iOS/AuthFeature/Sources/AuthFeature`

## Verification strategy

Задача считается готовой только при свежем сфокусированном доказательстве:
модульные тесты пакета проходят через ограничитель выполнения, статическая
проверка показывает только утверждённую верхнеуровневую публичную поверхность,
`AuthFlowView` создаётся от `AuthSessionModel`, а успешный вход или регистрация
переводит сессию в `.active`. Проверка также фиксирует обязанности
`package build`, `package consumer`, `consumer integration`, `public contract`,
`dependency graph`, `app-shell wiring`, `application boundary`, `cancellation`,
`isolation`, `cache policy`, `retry policy`, `simulator`, `accessibility`,
`design-system`, `platform-ux.md`, `Liquid Glass`, `light/dark`,
`increased contrast`, `Reduce Transparency`, `Reduce Motion` и
`older-OS/SDK fallback`, оставляя терминальные runtime-наблюдения для
последующей фазы `verify`.

После расширения текущего flow task-002 и task-003 закрывают незавершённый
хвост старого package без создания новой feature identity: приложение должно
импортировать только публичный контракт `AuthFeature`, показывать загрузку,
флоу или оболочку по `SessionState`, а UI-тесты должны запускать приложение с
детерминированной заглушкой без обращения к живому серверу.
