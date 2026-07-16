# task-001 — Доменный фундамент и манифест пакета

- Layer: domain
- Boundary owner: implementation-writer
- Engineering scopes: ["application", "package"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Discovered command: swift build --package-path iOS/AuthFeature
- Estimate (ideal): 0.5–1 days
- Paths: proposed: iOS/AuthFeature/Package.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/AuthConfiguration.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/SessionState.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/AuthError.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/AuthAPIClient.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/SessionSecretStore.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/TimeProvider.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/CheckEmailUseCase.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/LogInUseCase.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/RegisterAccountUseCase.swift; proposed: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/CheckSessionUseCase.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/AuthConfigurationTests.swift; proposed: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/AuthErrorTests.swift
- Read-only context: ["iOS/specs/user-profile-auth/changes/user-profile-auth/design.md", "iOS/specs/user-profile-auth/changes/user-profile-auth/implementation-spec.md", "iOS/workflow/rules/architecture/naming.md", "iOS/workflow/rules/architecture/types-clean-code.md", "iOS/workflow/rules/package-development.md", "iOS/workflow/rules/unit-testing.md"]

## Goal

Создать физическую единицу как отдельный пакет c доменными типами,
протокольными контрактами и протоколами вариантов использования. Закрепить
конфигурацию c проверкой адреса и семантику состояний и ошибок.

## Inline contract context

- `REQ-1` — приложение целиком за авторизацией, возможность подключается как внешняя единица.
- `REQ-4` — проверка сессии при запуске, хранение между запусками.
- `REQ-5` — ошибки флоу наблюдаемы и восстановимы.
- `REQ-6` — истечение или отзыв сессии возвращает на вход.
- `REQ-7` — пароль не сохраняется, сессионные данные хранятся недоступно.
- `AC-1` — запуск без валидной сессии открывает экран входа.
- `AC-10` — невалидная почта отклоняется до сетевого запроса.
- `AC-11` — короткий пароль при регистрации отклоняется до запроса.
- `AC-17` — после входа сохранённый пароль отсутствует.
- `AC-18` — сессионные данные недоступны другим приложениям.
- `IOS-REQ-9` — адрес передаётся композицией; конфигурация c проверкой схемы.
- `IOS-REQ-10` — контракт клиента покрывает четыре операции.
- `IOS-REQ-12` — возможность размещается в отдельном пакете.
- `AC-17` — пароль не сохраняется на устройстве.
- `AC-18` — сессионные данные хранятся недоступно другим приложениям.

## Implementation deliverables

- Манифест пакета c библиотечной целью и тестовой целью, привязанный к тулчейну и целевой платформе потребителя, c собственными настройками изоляции и диагностик.
- Тип конфигурации c полем адреса и инициализатором с проверкой, отклоняющим схему, отличную от защищённой, что делает невалидное состояние непредставимым на уровне типов.
- Перечисление состояния сессии c вариантами проверки, выхода c причиной и активности, а также причина завершения для маршрутизации истечения сессии.
- Перечисление доменных ошибок c вариантами неверных данных, занятой почты, проверки сервера, ограничения попыток, отсутствия сети, недействительности и сбоя, покрывающими весь конверт ответов.
- Протокольные контракты клиента, хранилища секрета и источника времени в папке домена, определяющие способность без привязки к реализации.
- Протоколы вариантов использования c явными сигнатурами и доменными возвращаемыми типами для проверки почты, входа, регистрации и проверки сессии.
- Тесты конфигурации, подтверждающие отклонение незащищённого адреса и принятие защищённого, а также тесты полноты вариантов ошибок и состояний.

## Steps

1. Создать каталог c подкаталогами домена, контрактов и вариантов использования.
2. Написать манифест: версия инструментов по установленному тулчейну, платформенный минимум по потребителю, библиотечная и тестовая цели.
3. Реализовать тип конфигурации c инициализатором, проверяющим схему адреса.
4. Реализовать перечисления состояний и ошибок как передаваемые типы.
5. Определить протоколы клиента, хранилища и источника времени.
6. Определить протоколы вариантов использования.
7. Написать тесты: отклонение незащищённого адреса, принятие защищённого, полнота вариантов.
8. Запустить сборку и тесты c watchdog 300 секунд.

## Verification

- Тесты конфигурации проходят: незащищённый адрес отклонён, защищённый принят.
- Тесты полноты ошибок и состояний подтверждают все варианты.
- Сборка успешна без предупреждений передаваемости.
- `application boundary` — домен не импортирует интерфейс и транспорт.
- `package consumer` — пакет собирается автономно.
- `consumer integration` — тестовая цель подключена.
- `package build` — сборка пакета успешна.
- `public contract` — только доменные типы и протоколы открыты.
- `dependency graph` — направление от домена к деталям.
- `app-shell wiring` — пакет не знает о потребителе.

## Expected result

Пакет собирается, тесты доменного фундамента проходят, открытый контракт
ограничен доменными типами и протоколами.

## Out of scope

Реализации клиента, хранилища и вариантов использования; транспорт;
интерфейс; интеграция c приложением.
