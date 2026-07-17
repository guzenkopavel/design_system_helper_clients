# task-001 — Минимальный публичный контракт AuthFeature

- Layer: infrastructure
- Boundary owner: implementation-writer отвечает за API пакета, фабричную композицию, сессионный шов флоу и сфокусированные тесты внутри iOS/AuthFeature.
- Engineering scopes: ["application", "concurrency", "networking", "package", "ui"]
- Depends on: none
- Status: done
- Evidence: evidence/task-001.md
- Estimate (ideal): 1–2 days
- Paths: existing: iOS/AuthFeature/.gitignore; existing: iOS/AuthFeature/Package.swift; existing: iOS/AuthFeature/Sources/AuthFeature/AuthFeatureFactory.swift; existing: iOS/AuthFeature/Sources/AuthFeature/AuthSessionModel.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/EmailCheckResponse.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/ErrorEnvelopeResponse.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/LoginResponse.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/ProfileResponse.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/DTO/RegisterResponse.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/DefaultAuthAPIClient.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Data/KeychainSessionSecretStore.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/AuthError.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/AuthAPIClient.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/SessionSecretStore.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/TimeProvider.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/SessionState.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/CheckEmailUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/CheckSessionUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultCheckEmailUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultCheckSessionUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultLogInUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/DefaultRegisterAccountUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/LogInUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/RegisterAccountUseCase.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/AuthFlowAction.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/AuthFlowState.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/AuthFlowView.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/AuthFlowViewModel.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/EmailStepView.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/FeedbackView.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/LoadingOverlay.swift; existing: iOS/AuthFeature/Sources/AuthFeature/Presentation/PasswordStepView.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/AuthFeatureFactoryTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/AuthSessionModelTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Data/DefaultAuthAPIClientTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Data/InMemorySessionSecretStore.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Data/KeychainSessionSecretStoreTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/CheckEmailUseCaseTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/CheckSessionUseCaseTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/LogInUseCaseTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Domain/UseCases/RegisterAccountUseCaseTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/EmailCheckSuccess.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorEmailConflict.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorInvalidCredentials.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorRateLimited.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorValidation.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/LoginSuccess.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ProfileSuccess.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/RegisterSuccess.json; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Presentation/AuthFlowViewModelTests.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Presentation/Fakes/FakeCheckEmailUseCase.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Presentation/Fakes/FakeLogInUseCase.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Presentation/Fakes/FakeRegisterAccountUseCase.swift; existing: iOS/AuthFeature/Tests/AuthFeatureTests/Presentation/Fakes/FakeTimeProvider.swift
- Read-only context: ["iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/design.md", "iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/implementation-spec.md", "iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/platform-ux.md", "iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/verification.md", "iOS/workflow/rules/architecture/dependency-injection.md", "iOS/workflow/rules/architecture/mvvm.md", "iOS/workflow/rules/package-development.md", "iOS/workflow/rules/swift-concurrency.md", "iOS/workflow/rules/unit-testing.md", "specs/product/user-profile-auth/spec.md", "specs/product/user-profile-auth/ux.md", "workflow/rules/test-execution.md"]

## Goal

Привести текущую частичную реализацию `AuthFeature` к утверждённому минимальному
публичному контракту пакета и закрыть главный разрыв task-007: фабрика, модель
сессии и флоу авторизации должны работать как единый композиционный шов, а
внутренние типы больше не должны быть видимы потребителю пакета.

## Inline contract context

- `REQ-1` — приложение целиком остаётся за авторизацией, а пакет предоставляет только точку композиции.
- `REQ-3` — успешный вход или регистрация немедленно открывают оболочку через активную сессию.
- `REQ-4` — запуск проверяет сессию и не показывает оболочку до активного состояния.
- `REQ-5` — состояния флоу остаются наблюдаемыми и восстановимыми.
- `REQ-6` — недействительная сессия возвращает на вход и очищает секрет.
- `REQ-8` — нативная UI-поверхность сохраняет ассистивную и визуальную семантику.
- `AC-5` — верные учётные данные открывают оболочку с активными «Кейсами».
- `AC-7` — повторный запуск в пределах жизни сессии открывает оболочку без входа.
- `AC-15` — истечение сессии возвращает на вход и скрывает данные прошлой сессии.
- `AC-19` — ассистивные имена и объявления соответствуют видимым состояниям.
- `IOS-REQ-4` — `AuthSessionModel.start()` идемпотентно проверяет сессию.
- `IOS-REQ-6` — успех флоу переводит модель сессии в `.active`.
- `IOS-REQ-8` — недействительность персонального запроса очищает секрет и возвращает `.signedOut`.
- `IOS-REQ-11` — асинхронный флоу сохраняет отмену, единственный активный запрос и изоляцию.
- `IOS-REQ-12` — публичный контракт пакета минимален и принадлежит отдельной физической единице.
- `IOS-AC-2` — UI сохраняет нативную семантику взаимодействия.
- `IOS-AC-7` — успех входа и регистрации закрывает флоу.
- `IOS-AC-12` — возврат по `401` очищает секрет.
- `IOS-AC-15` — конкурентность не создаёт дублирующих запросов.
- `IOS-AC-16` — граница `Swift package` и публичный программный интерфейс проверены статически.

## Implementation deliverables

- Минимальная верхнеуровневая публичная поверхность пакета содержит только утверждённые типы `AuthConfiguration`, `SessionState`, `AuthSessionModel`, `AuthFlowView` и `AuthFeatureFactory`, а внутренние протоколы, ошибки, варианты использования, модель представления, действия, состояния и контракты данных закрыты от потребителя.
- Согласованный сессионный шов флоу создаёт `AuthFlowView` от `AuthSessionModel`, передаёт зависимости фабричной композиции во внутреннюю модель представления и переводит модель сессии в активное состояние после успешного входа или регистрации.
- Сфокусированные тесты подтверждают статический публичный контракт, сценарии фабрики, идемпотентный запуск, недействительную сессию, успешное завершение флоу и отсутствие регрессии в конкурентном поведении модели представления.

## Steps

1. Заменить отдельный верхнеуровневый `SessionEndReason` на вложенную публичную причину внутри `SessionState`, чтобы верхнеуровневый `public contract` остался ровно из пяти типов.
2. Сделать `AuthError`, `AuthAPIClient`, `SessionSecretStore`, `TimeProvider`, протоколы вариантов использования, `AuthFlowAction`, `AuthFlowState` и `AuthFlowViewModel` внутренними, сохранив доступность для тестов через `@testable`.
3. Переделать `AuthFlowView` на публичный `init(sessionModel:)`; внутренняя модель представления должна создаваться из композиции пакета, а не передаваться потребителем.
4. Расширить `AuthSessionModel` внутренним фабричным швом для создания `AuthFlowViewModel` и публичными переходами сессии без раскрытия внутренних зависимостей.
5. Обновить `AuthFeatureFactory`: рабочий граф создаёт клиент, хранилище `Keychain`, варианты использования, модель сессии и построитель флоу; тестовые заглушки остаются `internal`.
6. Обновить сфокусированные тесты для фабрики, модели сессии и модели представления флоу, включая успешный переход флоу в сессию и обязательные маркеры проверки: `public contract`, `dependency graph`, `app-shell wiring`, `application boundary`, `package consumer`, `consumer integration`, `package build`, `cancellation`, `isolation`, `cache policy`, `retry policy`, `simulator`, `accessibility`, `design-system`, `platform-ux.md`, `Liquid Glass`, `light/dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion`, `older-OS/SDK fallback`.
7. Запустить `workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 90 --max-output-lines 6000 -- xcodebuild test -scheme AuthFeature-Package -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5'` из `iOS/AuthFeature`.
8. Выполнить статическую проверку `rg -n "public |open " iOS/AuthFeature/Sources/AuthFeature` и убедиться, что верхнеуровневая публичная поверхность соответствует дизайну.

## Verification

- `public contract`: статическая проверка показывает только пять утверждённых верхнеуровневых типов; вложенные публичные участники не раскрывают внутренние швы.
- `dependency graph`: фабрика зависит от внутренних абстракций `domain/data/presentation`, а потребитель приложения получает только публичные типы.
- `app-shell wiring`: `AuthFlowView` создаётся от `AuthSessionModel`, поэтому будущая корневая композиция не должна знать о модели представления или вариантах использования.
- `application boundary`: цель приложения по-прежнему остаётся владельцем `entry/lifecycle/root routing/DI/config/resources` и не получает реализацию авторизации.
- `package consumer`: пакет собирается с обновлённым публичным программным интерфейсом.
- `consumer integration`: тестовая цель использует `@testable import AuthFeature` для внутренних проверок и обычный совместимый с импортом публичный контракт.
- `package build`: тестовый прогон через ограничитель выполнения завершается успешно.
- `cancellation`: существующие тесты модели представления продолжают подтверждать отсутствие устаревших обновлений состояния.
- `isolation`: `AuthSessionModel` и состояние для UI остаются на `MainActor`, без `detached` и небезопасной изоляции.
- `cache policy`: очистка публичной поверхности не ослабляет решение сети и кэша `ephemeral` в `DefaultAuthAPIClient`.
- `retry policy`: флоу не добавляет автоматические повторы и сохраняет явное поведение повторной попытки.
- `simulator`: сфокусированный тест пакета использует назначение симулятора.
- `accessibility`: UI-тексты и подписи состояния не удаляются при смене шва инициализации.
- `design-system`: ремонт не добавляет локальные цвета, шрифты или декоративные controls.
- `platform-ux.md`: задача сохраняет решения READY platform UX как неизменяемый вход.
- `Liquid Glass`: задача не добавляет собственную стеклянную реализацию.
- `light/dark`: ремонт не вводит литералы, зависящие от оформления.
- `increased contrast`: ремонт не ломает использование семантических цветов.
- `Reduce Transparency`: ремонт не добавляет собственный blur или material fallback.
- `Reduce Motion`: ремонт не добавляет обязательные декоративные анимации.
- `older-OS/SDK fallback`: ремонт не вводит зависящий от availability программный интерфейс без fallback.

## Expected result

`AuthFeature` имеет минимальный публичный контракт, фабрика и модель сессии
компонуются без раскрытия внутренних типов, успешный флоу переводит состояние
сессии в `.active`, тесты пакета проходят через ограничитель, а новый пакет
остаётся готовым к последующей полной фазе `verify`.

## Out of scope

Интеграция `SysDevScenApp`, сквозные UI-тесты приложения, публикация durable
`SPECIFICATION.md`, изменение общей продуктовой спецификации, staging, commit и push.
