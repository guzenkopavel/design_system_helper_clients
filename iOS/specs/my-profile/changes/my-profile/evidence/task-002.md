# Доказательства задачи — task-002

## Итог

Создан изолированный пакет Swift `MyProfileFeature` с продуктом `MyProfileFeature`, целью `MyProfileFeature` и тестовой целью `MyProfileFeatureTests`. Пакет владеет доменными моделями профиля, владельцем состояния на `MainActor`, контрактом репозитория, клиентом API поверх стыка сессии из `AuthFeature`, последовательной пагинацией истории до `hasMore = false`, типизированным маппингом ошибок и сценарием выхода без логики оболочки приложения.

## Технические доказательства

iOS/MyProfileFeature/Package.swift | добавлен | пакет Swift с зависимостью только на локальный `AuthFeature`
iOS/MyProfileFeature/Sources/MyProfileFeature/Domain/MyProfileModels.swift | добавлен | доменные модели аккаунта, итогового профиля, состояния и типизированной ошибки
iOS/MyProfileFeature/Sources/MyProfileFeature/Domain/MyProfileRepository.swift | добавлен | граница репозитория для профиля, счётчика истории и выхода
iOS/MyProfileFeature/Sources/MyProfileFeature/Domain/MyProfileStateStore.swift | добавлен | владелец состояния на `MainActor` с защитой от дублирующего запроса и устаревшего обновления
iOS/MyProfileFeature/Sources/MyProfileFeature/Data/MyProfileAPIClient.swift | добавлен | клиент API через `AuthSessionRequesting`, построение запроса, пагинация и маппинг ошибок
iOS/MyProfileFeature/Tests/MyProfileFeatureTests/Data/MyProfileAPIClientTests.swift | добавлен | тесты построения запроса, пагинации, `401`, отсутствия сети и сбоя выхода
iOS/MyProfileFeature/Tests/MyProfileFeatureTests/Domain/MyProfileStateStoreTests.swift | добавлен | тесты полного счётчика, защиты от дубля, отмены и восстановления недействительной сессии

## Проверки

- RED-проверка единицы пакета: `bash workflow/scripts/test-watchdog.sh --max-seconds 180 --stall-seconds 45 --max-output-lines 25000 -- swift test --package-path iOS/MyProfileFeature` — PASS, первый запуск упал ожидаемо, потому что `iOS/MyProfileFeature` ещё отсутствовал.
- Фокусная проверка пакета: `bash workflow/scripts/test-watchdog.sh --max-seconds 180 --stall-seconds 45 --max-output-lines 25000 -- swift test --package-path iOS/MyProfileFeature` — PASS, 10 tests.
- Проверка scope: `workflow/scripts/validate-implementation-scope.py check --platform ios --feature my-profile --change my-profile --task task-002 --baseline iOS/specs/my-profile/changes/my-profile/evidence/scope-baseline-task-002.json --expected-sha256 coordinator-held-sha256` — PASS.

## Остаточные риски

Подключение продукта пакета к Xcode project, визуальная раскладка SwiftUI, локализованные resources и проверки simulator UI остаются в следующих областях задач. В текущей задаче потребитель пакета проверен на уровне графа зависимостей SwiftPM и публичной фабрики, без production edits в оболочке приложения.
