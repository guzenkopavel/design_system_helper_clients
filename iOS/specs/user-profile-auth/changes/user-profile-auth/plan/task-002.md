# task-002 — Сетевой клиент и конверт ошибок

- Layer: data
- Boundary owner: implementation-writer
- Engineering scopes: ["concurrency", "networking", "package"]
- Depends on: task-001
- Status: pending
- Evidence: none
- Estimate (ideal): 1–1.5 days
- Paths: proposed: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/EmailCheckResponse.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/LoginResponse.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/RegisterResponse.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/ProfileResponse.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/ErrorEnvelopeResponse.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Data/DefaultAuthAPIClient.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/DefaultAuthAPIClientTests.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/EmailCheckSuccess.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/LoginSuccess.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/RegisterSuccess.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/ProfileSuccess.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/ErrorInvalidCredentials.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/ErrorEmailConflict.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/ErrorValidation.json; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Data/Fixtures/ErrorRateLimited.json
- Read-only context: ["iOS/specs/user-profile-auth/changes/user-profile-auth/design.md", "iOS/specs/user-profile-auth/changes/user-profile-auth/implementation-spec.md", "iOS/workflow/rules/architecture/error-handling.md", "iOS/workflow/rules/ios-pitfalls.md", "iOS/workflow/rules/performance/networking.md", "iOS/workflow/rules/swift-concurrency.md"]

## Goal

Реализовать клиент поверх сеанса c временной конфигурацией, отключёнными
настройками и явным извлечением заголовков. Нормализовать конверт ошибок в
доменные типы. Тесты c заглушкой подтверждают четыре операции, отображение
ошибок, гарантию защищённого канала и политику настроек.

## Inline contract context

- `REQ-5` — ошибки флоу наблюдаемы и восстановимы, контракт клиента покрывает проверку, вход и регистрацию.
- `REQ-6` — истечение или отзыв сессии маршрутизируется через клиента.
- `REQ-7` — учётные данные передаются только по защищённому каналу.
- `AC-8` — неверный пароль показывает восстановимую ошибку.
- `AC-9` — пустое обязательное поле не отправляется.
- `AC-12` — ограничение попыток показывает время повтора.
- `AC-14` — отсутствие сети даёт восстановимое состояние.
- `IOS-REQ-9` — все запросы только по защищённому каналу; адрес из конфигурации.
- `IOS-REQ-10` — клиент покрывает проверку, вход, регистрацию и профиль; сессионная настройка предъявляется явным заголовком; ответ профиля маршрутизируется в недействительность.
- `AC-14` — отсутствие сети даёт восстановимое состояние с возможностью повторить.
- `AC-15` — истечение или отзыв сессии возвращает на вход c объяснением.

## Implementation deliverables

- Реализация клиента, соответствующая протоколу, c четырьмя операциями, построенными через структурные компоненты адреса без интерполяции пользовательского ввода в строку пути.
- Конфигурация сеанса c отключёнными настройками, кэшем и автоматическими политиками, что исключает попадание персональных данных в дисковые кэши.
- Декодирование конверта ошибок c полями кода, сообщения, повторяемости и трассировки и отображение статусов в доменные варианты c разбором заголовка повтора в обоих форматах.
- Извлечение значения сессионной настройки из заголовков ответа входа и регистрации и предоставление его как возвращаемого значения для последующего сохранения.
- Набор фиксур для каждого успешного ответа и типа ошибки, закреплённых в тестах как детерминированные входные данные.
- Тесты клиента, подтверждающие гарантию защищённого канала, отображение всех серверных ошибок, извлечение настройки, предъявление заголовка и маршрут недействительности.

## Steps

1. Создать подкаталоги данных и фиксур.
2. Реализовать типы ответов и конверт ошибок.
3. Реализовать клиент: инициализатор принимает конфигурацию и необязательный сеанс.
4. Построить адреса через структурные компоненты c путями операций.
5. Реализовать извлечение заголовков и разбор повтора.
6. Реализовать отображение статусов в доменные ошибки; проброс отмены без преобразования.
7. Написать фикстуры для каждого сценария.
8. Написать тесты: защищённый канал, отображение ошибок, извлечение настройки, маршрут недействительности.
9. Запустить тесты c watchdog 300 секунд.

## Verification

- Все тесты клиента проходят.
- Заглушка подтверждает: защищённый канал, корректные пути, отображение ошибок, извлечение настройки.
- `cache policy` — кэш отключён, настройки отключены.
- `retry policy` — автоматический повтор отсутствует; заголовок повтора соблюдается.
- `cancellation` — отмена запроса пробрасывается без преобразования.
- `isolation` — клиент передаваем, не удерживает мутабельное состояние.
- `package consumer` — пакет собирается c клиентом.
- `consumer integration` — тестовая цель подключена.
- `package build` — сборка успешна.
- `public contract` — клиент закрыт за протоколом.
- `dependency graph` — направление от данных к домену.
- `app-shell wiring` — клиент не знает о потребителе.

## Expected result

Клиент полностью покрывает контракт; все ошибки нормализованы; настройка
извлекается и предъявляется явно; тесты детерминированы c фикстурами.

## Out of scope

Хранилище; варианты использования; интерфейс; интеграция.
