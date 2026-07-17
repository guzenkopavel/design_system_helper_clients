# task-001 — Auth session seam

- Layer: infrastructure
- Boundary owner: AuthFeature session request boundary
- Engineering scopes: ["application", "networking", "package"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Estimate (ideal): 0.5-1 days
- Read-only context: ["iOS/AuthFeature/Package.swift", "iOS/specs/my-profile/changes/my-profile/design.md", "iOS/specs/my-profile/changes/my-profile/implementation-spec.md", "specs/product/my-profile/spec.md"]
- Paths: existing: iOS/AuthFeature/Sources/AuthFeature; existing: iOS/AuthFeature/Tests/AuthFeatureTests

## Goal

Открыть минимальный typed seam для запросов текущей серверной сессии и logout, не раскрывая Keychain storage, cookie secret или внутреннюю реализацию auth package.

## Inline contract context

`REQ-2`, `REQ-6`, `REQ-7`, `AC-2`, `AC-7`, `AC-10` и `AC-11` требуют profile/history/logout поверх текущей server session. `IOS-REQ-2`, `IOS-REQ-4`, `IOS-AC-3`, `IOS-AC-4` и `IOS-AC-6` требуют typed session client/provider, mapping 401 в восстановление и безопасный logout route.

## Implementation deliverables

- Публичный session seam отдаёт профильной feature только возможность запроса текущей сессии.
- Тесты `AuthFeature` подтверждают передачу cookie, маршрут logout и mapping недействительной сессии.

## Steps

Добавить в `AuthFeature` публичный `typed contract` для `session-bound HTTPS request` или `minimal session provider`, достаточный для `GET /api/profile`, `GET /api/interviews/history` и `POST /api/auth/logout`. Сохранить детали Keychain и token закрытыми внутри package. Добавить `focused tests` до implementation для `public contract`, `request cookie behavior`, `401 mapping` и `logout failure recovery`. Проверить `package consumer expectation`, `consumer integration` и `app-shell wiring`: `AuthFeature` не зависит от `MyProfileFeature` или `application shell`.

## Verification

- Discovered command: `swift test --package-path iOS/AuthFeature`
- Watchdog max/stall/output budget for nontrivial checks: max 120s, stall 30s, output 20000 lines
- Applicable rule/check mapping: `package consumer`, `consumer integration`, `package build`, `public contract`, `dependency graph`, `app-shell wiring`, `cache policy`, `retry policy`, `application boundary`

## Expected result

`swift test --package-path iOS/AuthFeature` проходит, public API остаётся минимальным, session secret не логируется и не раскрывается, а 401/logout failures имеют typed recovery path для следующей задачи.

## Out of scope

UI профиля, package `MyProfileFeature`, проводка Xcode project и simulator checks не входят в эту задачу.
