# Plan — my-profile / iOS / my-profile

## Planning frame

План строится от валидного пакета `specified` по пути `iOS/specs/my-profile/changes/my-profile` с `design_gate: PASS`, пустыми блокерами и полным контрактом после изменения в `implementation-spec.md`. Feature-root `iOS/specs/my-profile/SPECIFICATION.md` отсутствует, поэтому неизменяемый текущий baseline для этой feature-root не применим; baseline поведения берётся из одобренной общей продуктовой спеки и iOS-артефактов пакета. Production code этим планом не изменяется.

## Revalidated engineering scopes and exact rules

- Selection snapshot: `plan/rule-selection.json`
- Engineering scopes: `["application", "concurrency", "localization", "networking", "package", "ui"]`
- Applicable rule files: exact lifecycle union from `workflow/scripts/find-platform-context.py --phase plan --platform iOS --feature my-profile --change my-profile`
- Selection evidence: `application` нужен для композиции вкладки и восстановления авторизации; `package` нужен для физической границы `MyProfileFeature`; `networking` нужен для `GET /api/profile`, `GET /api/interviews/history` и `POST /api/auth/logout`; `concurrency` нужен для `MainActor`, отмены задач и пагинации; `ui` нужен для SwiftUI-поверхности и проверок симулятора; `localization` нужен для русских строк без грамматически опасной конкатенации.

## Assumptions

Адрес API остаётся внешним значением конфигурации, обнаруженным в `SysDevScenApp`. Новый package использует нижнюю границу iOS не ниже существующего шаблона package и проверяет доступность возможностей SDK при реализации. Живой backend не является обязательным доказательством PASS; фокусные тесты и фикстуры симулятора дают детерминированные доказательства.

## DAG

`task-001` готов без зависимостей и создаёт session seam в `AuthFeature`.

`task-002` зависит от `task-001` и создаёт package `MyProfileFeature` с доменной моделью, сетевым слоем, правилами конкурентности и тестами package.

`task-003` зависит от `task-002` и добавляет SwiftUI-presentation, ресурсы локализации и нативное UX-поведение внутри package.

`task-004` зависит от `task-003` и подключает потребителя package, проводку app-shell, интеграцию проекта и UI/runtime-проверки.

## Tasks

- `task-001`: typed session seam в `AuthFeature`, чтобы профильная feature не знала реализацию Keychain.
- `task-002`: изолированный пакет `MyProfileFeature` для API профиля, пагинации, машины состояния, восстановления выхода и модульных тестов.
- `task-003`: представление SwiftUI и локализация внутри `MyProfileFeature` по `platform-ux.md`.
- `task-004`: интеграция потребителя Xcode, композиция app-shell и покрытие UI-тестами.

## Estimates and multipliers

Оценки учитывают создание нового пакета, обнаруженную проводку проекта и неопределённость UI/runtime-проверок. Каждая задача остаётся в пределах двух ideal days: `session seam` занимает `0.5-1`, слой `domain/data package` занимает `1.5-2`, слой `presentation/localization` занимает `1-1.5`, а `consumer integration` и `UI tests` занимают `1-2`.

## Verification strategy

Использовать TDD-first по task scope: сначала фокусные unit tests для seam, API requests, pagination, переходов состояния и отмены, затем package build, затем consumer build и UI-проверки в симуляторе. Основные обнаруженные команды: `swift test --package-path iOS/AuthFeature`, `swift test --package-path iOS/MyProfileFeature`, `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' build`, `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' test`.

## Test and performance budgets

Нетривиальные проверки используют конечные watchdog limits: `swift test --package-path iOS/AuthFeature` максимум 120 секунд, stall 30 секунд, вывод 20000 lines; `swift test --package-path iOS/MyProfileFeature` максимум 180 секунд, stall 45 секунд, вывод 25000 lines; `xcodebuild ... build` максимум 300 секунд, stall 60 секунд, вывод 40000 lines; `xcodebuild ... test` максимум 600 секунд, stall 90 секунд, вывод 60000 lines. Networking performance budget: пагинация идёт последовательными страницами, параллельный дубликат history request запрещён, retry policy явно не делает automatic retry без действия пользователя. Concurrency performance budget: cancellation предотвращает устаревшее обновление UI после ухода владельца.

## Checkpoints

Перед переходом к UI убедиться, что проходят `package public contract` и `visibility tests`. Перед `app-shell wiring` убедиться, что `dependency graph` не направляет feature обратно в `application shell`. Перед доказательствами симулятора проверить обязательства `platform-ux.md`: `Liquid Glass`, `light/dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion` и `older-OS/SDK fallback`.

## Risks

Проводка Xcode project может потребовать аккуратного обновления `project.pbxproj`; это ограничено task-004. Доступность Liquid Glass может отличаться от ожиданий SDK; fallback должен сохранять product outcome. Существующий auth API client сейчас владеет деталями session storage, поэтому task-001 обязан оставить Keychain закрытым и открыть только typed session request/logout seam.
