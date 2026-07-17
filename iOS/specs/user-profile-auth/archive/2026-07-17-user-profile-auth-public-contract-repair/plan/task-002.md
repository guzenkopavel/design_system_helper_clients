# task-002 — Интеграция AuthFeature в приложение

- Layer: infrastructure
- Boundary owner: implementation-writer отвечает за корневую композицию приложения, подключение локального пакета и тестовый режим заглушки без переноса реализации авторизации в цель приложения.
- Engineering scopes: ["application", "package"]
- Depends on: task-001
- Status: done
- Evidence: evidence/task-002.md
- Estimate (ideal): 1–1.5 days
- Paths: existing: iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj; existing: iOS/SysDevScen/SysDevScen/RootView.swift; existing: iOS/SysDevScen/SysDevScen/SysDevScenApp.swift; existing: iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift
- Read-only context: ["iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/design.md", "iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/implementation-spec.md", "iOS/specs/user-profile-auth/changes/user-profile-auth-public-contract-repair/platform-ux.md", "iOS/workflow/rules/app-development.md", "iOS/workflow/rules/architecture/dependency-injection.md", "iOS/workflow/rules/architecture/feature-first.md", "iOS/workflow/rules/architecture/legacy.md", "iOS/workflow/rules/ios-pitfalls.md", "iOS/workflow/rules/package-development.md"]

## Goal

Подключить `AuthFeature` к `SysDevScen` и заменить прямой запуск оболочки
корневой маршрутизацией по состоянию сессии. Цель приложения остаётся
composition shell: она создаёт конфигурацию, выбирает live или stub модель и
показывает ровно одну поверхность — загрузку, флоу авторизации или существующую
оболочку.

## Inline contract context

- `REQ-1` — приложение целиком остаётся за авторизацией, а корневая композиция владеет только входом и маршрутизацией.
- `REQ-3` — успех входа или регистрации немедленно открывает оболочку через активную сессию.
- `REQ-4` — запуск проверяет сессию и не показывает оболочку до активного состояния.
- `AC-1` — запуск без валидной сессии открывает экран входа.
- `AC-5` — верные учётные данные открывают оболочку с активными «Кейсами».
- `AC-7` — повторный запуск в пределах жизни сессии открывает оболочку без входа.
- `IOS-REQ-1` — приложение владеет только входом, жизненным циклом, маршрутизацией и связыванием зависимостей.
- `IOS-REQ-4` — запуск показывает загрузку, валидная сессия ведёт в оболочку, отсутствие сессии ведёт во флоу.
- `IOS-REQ-6` — успех флоу заменяет корневую поверхность оболочкой.
- `IOS-REQ-12` — возможность `AuthFeature` подключается как отдельная физическая единица.
- `IOS-AC-1` — статическая проверка подтверждает владение гейтом и композицией.
- `IOS-AC-4` — запуск без сессии показывает загрузку, затем шаг почты.
- `IOS-AC-7` — успешные вход и регистрация открывают оболочку с «Кейсами».
- `IOS-AC-16` — граница Swift package и граф зависимостей проверены.

## Implementation deliverables

- Корневая точка входа создаёт `AuthSessionModel` через `AuthFeatureFactory`, выбирая живую конфигурацию из окружения или детерминированный режим заглушки по аргументу запуска, и вызывает идемпотентный запуск сессии.
- Новый `RootView` принимает модель сессии и отображает загрузку, `AuthFlowView` или существующую `ContentView` по `SessionState`, не добавляя реализацию сети, хранения или флоу в application target.
- Манифест пакета публикует library product `AuthFeature`, а файл проекта подключает локальный пакет `iOS/AuthFeature` к цели приложения так, чтобы сборка потребителя доказывала `package consumer`, `consumer integration`, `package build`, `public contract`, `dependency graph` и `app-shell wiring`.
- Существующие shell `UI` тесты запускают активный сценарий заглушки, чтобы после интеграции продолжать проверять оболочку без прохождения авторизации.

## Steps

1. Расширить публичный контракт `AuthFeatureFactory` вложенным сценарием заглушки и публичным методом создания модели заглушки без открытия внутренних типов.
2. Опубликовать library product `AuthFeature`, подключить локальный Swift package `iOS/AuthFeature` в `SysDevScen.xcodeproj` и добавить продукт `AuthFeature` в цель приложения.
3. Создать `RootView` с `@ObservedObject` моделью сессии, состоянием загрузки и переключением `.checking`, `.signedOut`, `.active`.
4. Обновить `SysDevScenApp`: создать модель сессии, прочитать `AUTH_API_BASE_URL`, поддержать аргументы запуска для сценариев заглушки и заменить `ContentView()` на `RootView`.
5. Обновить shell UI-тесты так, чтобы они явно запускали активную сессию заглушки и продолжали проверять разделы оболочки.
6. Запустить сборку приложения через `test-watchdog.sh` c лимитом 300 секунд.
7. Запустить существующий UI suite через `test-watchdog.sh` c лимитом 300 секунд.

## Verification

- `application boundary`: цель приложения содержит только композицию, маршрутизацию, жизненный цикл и конфигурацию.
- `package consumer`: `SysDevScen` подключает локальный пакет `AuthFeature`.
- `consumer integration`: приложение собирается с импортом публичного контракта.
- `package build`: сборка приложения тянет и собирает пакет.
- `public contract`: цель приложения использует только `AuthFeatureFactory`, `AuthConfiguration`, `AuthSessionModel`, `AuthFlowView` и `SessionState`.
- `dependency graph`: зависимость направлена от приложения к пакету, обратной зависимости нет.
- `app-shell wiring`: `RootView` показывает загрузку, флоу или оболочку по состоянию сессии.
- `simulator`: набор UI-тестов запускается на `iPhone 17 Pro, OS=26.5`.

## Expected result

Приложение запускается через авторизационный gate: без сессии показывает флоу,
с активной сессией заглушки показывает существующую оболочку, а живая
конфигурация остаётся готовой к проверке реального backend-контракта.

## Out of scope

Новые сквозные сценарии UI авторизации, проверка живого сервера, terminal verification,
staging, commit и push.
