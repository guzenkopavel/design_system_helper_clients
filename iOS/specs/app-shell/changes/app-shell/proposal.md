# iOS proposal — app shell

## Intake

Пакет с продуктовой основой принимает утверждённый общий договор из
`specs/product/app-shell/spec.md`. В его метаданных указаны `READY` и
`APPROVED`, а проверка `validate-product-spec.py check --feature app-shell`
возвращает `PASS`.

## Goal

Заменить технический первый экран iOS на корневую композицию приложения,
которая реализует утверждённый shell, остаётся в границе приложения и даёт
понятные точки проверки для нативного интерфейса.

## Scope

В объём входят найденные `SysDevScenApp`, корневой SwiftUI-экран, замена
технического Core Data списка, корневая маршрутизация и нативная семантика
управления. Реализация использует существующие цели приложения, модульных
тестов и UI-тестов; визуальная адаптация iOS закреплена в `platform-ux.md`.

## Engineering scope selection

- `application` выбран по существующему
  `iOS/SysDevScen/SysDevScen/SysDevScenApp.swift` и единственной production-цели
  `SysDevScen` в `iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj`: изменение
  начинается на границе входа и сборки корня приложения.
- `ui` выбран по существующему
  `iOS/SysDevScen/SysDevScen/ContentView.swift`: это текущая SwiftUI-поверхность,
  которую заменит реализация утверждённого поведения.
- `package` не выбран: shell является локальной корневой композицией и
  маршрутизацией. Поиск не нашёл существующий Swift package или production-единицу
  вне приложения, а признаки отдельной capability отсутствуют.
- `concurrency`, `performance`, `networking`, `startup`, `memory`, `rendering`,
  `localization`, `xcode`, `simulator`, `delivery` и `developer-experience` не
  выбраны: изменение не добавляет такие возможности и не создаёт отдельного
  владения; нужные runtime-проверки интерфейса приходят из выбранного `ui`.

## Applicable rule files

Точный набор правил для фазы proposal и выбранных областей:

- `workflow/rules/specification-layers.md`
- `workflow/rules/artifact-language.md`
- `workflow/rules/system-design.md`
- `workflow/rules/system-design/modularity.md`
- `iOS/workflow/rules/architecture.md`
- `iOS/workflow/rules/package-development.md`
- `workflow/rules/coding-standards.md`
- `workflow/rules/tdd-first.md`
- `workflow/rules/test-execution.md`
- `workflow/rules/verification-matrix.md`
- `workflow/rules/code-comments.md`
- `iOS/workflow/rules/swift-style.md`
- `workflow/rules/verification-evidence.md`
- `iOS/workflow/rules/app-development.md`
- `iOS/workflow/rules/ios-pitfalls.md`
- `iOS/workflow/rules/architecture/feature-first.md`
- `iOS/workflow/rules/architecture/dependency-injection.md`
- `iOS/workflow/rules/architecture/use-cases.md`
- `iOS/workflow/rules/architecture/error-handling.md`
- `iOS/workflow/rules/architecture/naming.md`
- `iOS/workflow/rules/architecture/legacy.md`
- `iOS/workflow/rules/architecture/types-clean-code.md`
- `iOS/workflow/rules/unit-testing.md`
- `iOS/workflow/rules/accessibility.md`
- `iOS/workflow/rules/ui-design-system.md`
- `iOS/workflow/rules/ui-testing.md`
- `iOS/workflow/rules/ui-test-spec.md`
- `iOS/workflow/rules/simulator.md`
- `iOS/workflow/rules/architecture/mvvm.md`

## Non-goals

Не входят данные, хранение, сеть, вход в аккаунт, аналитика, внешняя навигация,
новая переиспользуемая UI-возможность, перестройка проекта и изменения Android.
План, production-код и выделение отдельного package/target в этой фазе также не
создаются.

## Accepted decisions

iOS-реализация опирается на найденные SwiftUI-точку входа и корневую сборку.
`ContentView.swift` считается существующим техническим шаблоном, а не
доказательством нужной продуктовой архитектуры; путь его замены остаётся
предложенным до Implement. Общий observable-договор остаётся единственным
источником продуктового поведения, а платформенный пакет добавляет только iOS
integration, владение и контекст проверки.

## Open questions

Нет открытых вопросов.

## Risks

Текущий шаблон импортирует Core Data и показывает действия со списком и
хранением, несовместимые с утверждённым инкрементом. До реализации нужно
обнаружить scheme/runtime и использовать READY `platform-ux.md`; без этого
нельзя утверждать нативный вид, accessibility или simulator evidence.
