# task-002 — Profile package core

- Layer: data
- Boundary owner: MyProfileFeature Swift package boundary
- Engineering scopes: ["concurrency", "networking", "package"]
- Depends on: task-001
- Status: done
- Evidence: evidence/task-002.md
- Estimate (ideal): 1.5-2 days
- Read-only context: ["iOS/AuthFeature/Package.swift", "iOS/specs/my-profile/changes/my-profile/design.md", "iOS/specs/my-profile/changes/my-profile/implementation-spec.md", "specs/product/my-profile/spec.md"]
- Paths: proposed: iOS/MyProfileFeature/Package.swift; proposed: iOS/MyProfileFeature/Sources/MyProfileFeature/Data; proposed: iOS/MyProfileFeature/Sources/MyProfileFeature/Domain; proposed: iOS/MyProfileFeature/Tests/MyProfileFeatureTests/Data; proposed: iOS/MyProfileFeature/Tests/MyProfileFeatureTests/Domain

## Goal

Создать isolated Swift package `MyProfileFeature`, который владеет доменной моделью профиля, DTO, API client, pagination, logout use case, машиной состояния и package-level tests.

## Inline contract context

`REQ-1`, `REQ-2`, `REQ-3`, `REQ-5`, `REQ-7`, `AC-1`, `AC-2`, `AC-3`, `AC-6`, `AC-9`, `AC-10` и `AC-11` задают наблюдаемые данные профиля, полный счётчик интервью, недоступные состояния и восстановление. `IOS-REQ-1`, `IOS-REQ-2`, `IOS-REQ-3`, `IOS-REQ-4`, `IOS-REQ-6`, `IOS-AC-1`, `IOS-AC-3`, `IOS-AC-4` и `IOS-AC-8` требуют `package isolation`, `typed API`, `pagination`, `single active request`, `cancellation` и восстановление недействительной сессии.

## Implementation deliverables

- Package `MyProfileFeature` содержит `typed domain state`, `API client` и владельца `pagination`.
- Модульные тесты доказывают `request construction`, `full-count pagination` и `cancellation isolation`.

## Steps

Создать `iOS/MyProfileFeature/Package.swift` по обнаруженному шаблону package `AuthFeature` и добавить targets `MyProfileFeature` и `MyProfileFeatureTests`. Реализовать DTO, `repository/API client`, use cases и `MainActor state owner` без `SwiftUI-specific rendering`. Построить URLs через structured `URLComponents`, требовать HTTPS, передавать `session-bound dependency` из task-001, не хранить `email/history details` после invalid session. Для `pagination` последовательно загружать страницы до `page.hasMore = false`, поддерживать `cancellation` между страницами и `single active request policy`. Сначала добавить `focused tests` на `request construction`, `401 mapping`, `offline mapping`, `logout failure`, `duplicate request prevention` и `stale update prevention`. Проверить `package consumer`, `consumer integration` и `app-shell wiring` как будущий контракт потребителя без зависимости на `application shell`.

## Verification

- Discovered command: `swift test --package-path iOS/MyProfileFeature`
- Watchdog max/stall/output budget for nontrivial checks: max 180s, stall 45s, output 25000 lines
- Applicable rule/check mapping: `package consumer`, `consumer integration`, `package build`, `public contract`, `dependency graph`, `app-shell wiring`, `module-level tests`, `cache policy`, `retry policy`, `cancellation`, `isolation`, `performance budget`

## Expected result

`swift test --package-path iOS/MyProfileFeature` проходит, package имеет минимальный `public API/factory`, `dependency graph` направлен к `session seam`, networking имеет `explicit cache policy` and `retry policy`, а `cancellation` не обновляет устаревшее UI-состояние.

## Out of scope

`SwiftUI visual layout`, `localized resources`, `Xcode app integration` и `simulator UI tests` остаются для последующих задач.
