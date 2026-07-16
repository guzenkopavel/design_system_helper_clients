# task-008 — Интеграция c приложением и корневая композиция

- Layer: infrastructure
- Boundary owner: implementation-writer
- Engineering scopes: ["application", "package"]
- Depends on: task-007
- Status: done
- Evidence: evidence/reconciliation-task-008.md
- Discovered command: xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
- Estimate (ideal): 1–1.5 days
- Paths: existing: iOS/SysDevScen/SysDevScen/SysDevScenApp.swift; existing: iOS/SysDevScen/SysDevScen/ContentView.swift; existing: iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj; existing: iOS/SysDevScen/SysDevScenTests/SysDevScenTests.swift; existing: iOS/SysDevScen/SysDevScenUITests/SysDevScenUITests.swift; proposed: iOS/SysDevScen/SysDevScen/RootView.swift; proposed: iOS/SysDevScen/SysDevScenTests/AppShellStateTests.swift; proposed: iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift
- Read-only context: ["iOS/specs/user-profile-auth/changes/user-profile-auth/design.md", "iOS/specs/user-profile-auth/changes/user-profile-auth/implementation-spec.md", "iOS/workflow/rules/app-development.md", "iOS/workflow/rules/architecture/dependency-injection.md", "iOS/workflow/rules/architecture/feature-first.md", "iOS/workflow/rules/architecture/legacy.md", "iOS/workflow/rules/ios-pitfalls.md", "iOS/workflow/rules/package-development.md"]

## Goal

Добавить пакет как зависимость в проект и модифицировать корневую композицию
для проверки сессии при запуске. Создать корневой вид c маршрутизацией трёх
поверхностей: загрузка, флоу, оболочка. Базовая оболочка не меняется. Тесты
подтверждают владение композицией.

## Inline contract context

- `REQ-1` — приложение целиком за авторизацией, корневая композиция владеет только входом и маршрутизацией.
- `REQ-3` — успех входа или регистрации немедленно открывает оболочку.
- `REQ-4` — проверка сессии при запуске, хранение между запусками.
- `AC-1` — запуск без валидной сессии открывает экран входа.
- `AC-5` — верные учётные данные открывают оболочку.
- `AC-7` — перезапуск в пределах жизни сессии открывает оболочку без входа.
- `IOS-REQ-1` — приложение владеет только входом, жизненным циклом, маршрутизацией и связыванием; возможность подключается как внешняя единица.
- `IOS-REQ-4` — запуск показывает загрузку; валидная сессия — оболочка; иначе — флоу.
- `IOS-REQ-6` — успех флоу — оболочка c разделом кейсов; возврат невозможен.
- `AC-1` — запуск без валидной сессии открывает экран входа c полем почты, навигация оболочки не отображается.
- `AC-3` — успешные вход и регистрация немедленно открывают оболочку c активным разделом кейсов.

## Implementation deliverables

- Модификация точки входа, создающая конфигурацию из внешнего параметра окружения, получающая модель сессии из фабрики и вызывающая запуск идемпотентно, без реализации возможностей в целевой области приложения.
- Новый корневой вид, принимающий модель сессии и отображающий ровно одну из трёх поверхностей по состоянию: спокойное состояние загрузки при проверке, вид флоу при выходе и существующую оболочку при активности, c заменой корневого дерева без истории навигации.
- Модификация файла проекта для добавления пакета как локальной зависимости c подключением библиотечной цели к целевой области приложения и тестовым целям.
- Тесты целевой области, подтверждающие маршрутизацию трёх поверхностей по состоянию и отсутствие реализации возможностей в целевой области приложения.

## Steps

1. Добавить пакет как локальную зависимость в файл проекта: удалённая ссылка и продуктовая зависимость для библиотечной цели.
2. Подключить пакет к целям приложения и тестов.
3. Создать корневой вид c моделью сессии и переключением по состоянию.
4. Модифицировать точку входа: создать конфигурацию c адресом из окружения; создать модель через фабрику; заменить содержимое на корневой вид.
5. Добавить аргумент запуска для заглушки: аргументы процесса содержат заглушку — фабрика создаёт заглушку.
6. Написать тесты: корневой вид при проверке показывает загрузку; при выходе показывает флоу; при активности показывает оболочку.
7. Запустить сборку c watchdog 300 секунд.
8. Запустить тесты c watchdog 300 секунд.

## Verification

- Сборка приложения c пакетом успешна.
- `application boundary` — целевая область не содержит реализации возможностей.
- `package consumer` — пакет подключён как зависимость.
- `consumer integration` — приложение собирается c пакетом.
- `app-shell wiring` — корневая композиция показывает три поверхности.
- `dependency graph` — направление от приложения к пакету.
- `package build` — сборка пакета успешна.
- `public contract` — открытый контракт используется корректно.

## Expected result

Приложение c проверкой сессии при запуске: загрузка, затем флоу или оболочка;
базовая оболочка не изменена; реализация только в пакете.

## Out of scope

Тесты интерфейса потребителя; проход паритета.
