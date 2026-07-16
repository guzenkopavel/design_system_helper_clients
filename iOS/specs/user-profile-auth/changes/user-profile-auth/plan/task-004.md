# task-004 — Реализация вариантов использования

- Layer: domain
- Boundary owner: implementation-writer
- Engineering scopes: ["application", "concurrency"]
- Depends on: task-001, task-002, task-003
- Status: pending
- Evidence: none
- Estimate (ideal): 1–1.5 days
- Paths: proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultCheckEmailUseCase.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultLogInUseCase.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultRegisterAccountUseCase.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultCheckSessionUseCase.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/CheckEmailUseCaseTests.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/LogInUseCaseTests.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/RegisterAccountUseCaseTests.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/CheckSessionUseCaseTests.swift
- Read-only context: ["iOS/specs/user-profile-auth/changes/user-profile-auth/design.md", "iOS/specs/user-profile-auth/changes/user-profile-auth/implementation-spec.md", "iOS/workflow/rules/architecture/error-handling.md", "iOS/workflow/rules/architecture/use-cases.md", "iOS/workflow/rules/swift-concurrency.md", "iOS/workflow/rules/unit-testing.md"]

## Goal

Реализовать четыре варианта использования поверх протокольных контрактов.
Каждый получает зависимости через инициализатор, не знает о конкретном
транспорте и хранилище, и возвращает доменные типы. Тесты c подделками
подтверждают корректность делегирования, нормализацию ошибок и маршрут
недействительности персонального запроса.

## Inline contract context

- `REQ-1` — приложение целиком за авторизацией, варианты использования обеспечивают проверку и вход.
- `REQ-4` — проверка сессии при запуске, хранение между запусками.
- `REQ-5` — ошибки флоу наблюдаемы и восстановимы через варианты использования.
- `REQ-6` — истечение или отзыв сессии маршрутизируется через проверку сессии.
- `AC-5` — верные учётные данные открывают оболочку.
- `AC-6` — валидная новая пара создаёт аккаунт и открывает оболочку.
- `AC-7` — перезапуск в пределах жизни сессии открывает оболочку без входа.
- `AC-15` — истечение сессии возвращает на вход.
- `IOS-REQ-4` — проверка сессии читает секрет; при отсутствии — выход; при наличии — профиль; успех — активность; недействительность — очистка.
- `IOS-REQ-5` — проверка почты вызывает клиента и возвращает ветвление; вход и регистрация вызывают клиента и возвращают секрет.
- `IOS-REQ-10` — недействительность персонального запроса маршрутизируется.
- `AC-1` — запуск без валидной сессии открывает экран входа c полем почты.
- `AC-7` — перезапуск в пределах жизни сессии открывает оболочку без экрана входа.

## Implementation deliverables

- Реализация проверки почты, делегирующая клиенту и возвращающая доменный результат ветвления без знания о конкретном транспорте или формате ответов.
- Реализация входа, вызывающая клиента c почтой и паролем, сохраняющая секрет через хранилище и возвращающая успешный результат без повторной отправки при блокировке.
- Реализация регистрации, вызывающая клиента c почтой и паролем, сохраняющая секрет и возвращающая успешный результат c тем же контрактом хранения.
- Реализация проверки сессии, читающая секрет из хранилища, выполняющая профиль при наличии секрета и маршрутизирующая ответ недействительности в очистку хранилища c доменным возвратом.
- Тесты всех четырёх вариантов c подделками, подтверждающие корректное делегирование, сохранение секрета при успехе, очистку при недействительности и проброс ошибок без маскировки.

## Steps

1. Создать файлы реализаций в папке вариантов использования.
2. Каждый вариант — передаваемая структура c протокольными зависимостями через инициализатор.
3. Проверка почты: делегирование клиенту, возврат доменного результата.
4. Вход: вызов клиента, сохранение секрета, возврат успеха.
5. Регистрация: аналогично c регистрацией.
6. Проверка сессии: чтение секрета, при наличии — профиль, при недействительности — очистка и возврат.
7. Написать подделки клиента и хранилища c настраиваемыми результатами.
8. Написать тесты: проверка без секрета, все варианты делегируют корректно, недействительность — очистка, ошибки пробрасываются.
9. Запустить тесты c watchdog 300 секунд.

## Verification

- Все тесты вариантов использования проходят c подделками.
- `cancellation` — ошибка отмены пробрасывается без преобразования.
- `isolation` — варианты передаваемы, не удерживают мутабельное состояние.
- `application boundary` — варианты не импортируют интерфейс и транспорт.
- `package consumer` — пакет собирается c вариантами.
- `consumer integration` — тестовая цель подключена.
- `package build` — сборка успешна.
- `public contract` — варианты закрыты за протоколами.
- `dependency graph` — направление от домена к деталям.
- `app-shell wiring` — варианты не знают о потребителе.

## Expected result

Четыре варианта полностью реализованы и протестированы; каждый покрывает
свой контракт и нормализует ошибки в доменные типы.

## Out of scope

Интерфейс; автомат состояний; интеграция c приложением.
