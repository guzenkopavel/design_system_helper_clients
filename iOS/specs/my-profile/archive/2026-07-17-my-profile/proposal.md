# Proposal — my-profile / iOS / my-profile

## Intake

- Change type: product-backed
- Shared product spec: `specs/product/my-profile/spec.md`
- Product status / approval: READY / APPROVED
- Product impact assessment: PRESENT
- Evidence: общая спека `my-profile` прошла product gate и требует наблюдаемое iOS-поведение вкладки профиля, истории интервью и выхода.
- Tier: standard

## Goal

Создать iOS implementation package для фичи `my-profile`, который описывает
полный post-change контракт платформы до планирования и реализации. Пакет
должен связать READY shared spec с текущей iOS оболочкой, существующим
auth-baseline и новым изолированным профильным capability без записи
production-кода.

## Scope

- Вкладка `Профиль` в существующем `TabView` получает композицию профильного
  экрана вместо текущей заглушки.
- Новая platform capability получает профильный экран, загрузку текущего email,
  постраничную историю интервью, вычисление полного количества, краткое
  сообщение и действие выхода.
- Auth/session seam должен позволить profile capability использовать текущую
  серверную сессию и возвращать shell в signed-out auth-flow после logout или
  invalid session.
- Пакет iOS должен покрыть состояние SwiftUI, асинхронную сеть, отмену задач,
  русские строки, доступность, адаптацию Liquid Glass и simulator/UI evidence
  в будущих phase.

## Engineering scope selection

- Selected scopes: `application`, `concurrency`, `localization`, `networking`, `package`, `ui`
- Evidence for each scope:
  - `application`: `iOS/SysDevScen/SysDevScen/ContentView.swift` владеет текущей
    вкладочной композицией, а `RootView.swift` связывает active session с shell.
  - `ui`: shared UX задаёт новый экран, состояния, краткое сообщение,
    accessibility и appearance obligations.
  - `networking`: shared spec требует `GET /api/profile`,
    `GET /api/interviews/history` с пагинацией и `POST /api/auth/logout`.
  - `localization`: все видимые строки на русском и требуют контролируемой
    iOS-подачи без конкатенации пользовательских фраз.
  - `concurrency`: профиль загружает профиль и страницы истории async, должен
    отменять работу при уходе owner и не обновлять UI вне `MainActor`.
- Considered but not selected:
  - `package`: новая feature получает отдельный Swift package по strong default,
    поэтому scope выбран явно вместе с base rule.
  - `performance`: отдельный бюджет производительности не задан; networking
    scope уже фиксирует ограниченную пагинацию и политику повторных запросов.
  - `startup`: фича активируется при входе во вкладку профиля, cold launch SLO
    не меняется.
  - `memory`, `rendering`, `xcode`, `simulator`, `delivery`,
    `developer-experience`: применимые проверки будут выведены из выбранных
    scopes и phase, но самостоятельного evidence для scope нет.

## Applicable rule files

Точный набор правил жизненного цикла из базового этапа и выбранных областей:

- `workflow/rules/specification-layers.md`
- `workflow/rules/artifact-language.md`
- `workflow/rules/system-design.md`
- `workflow/rules/system-design/modularity.md`
- `iOS/workflow/rules/architecture.md`
- `iOS/workflow/rules/package-development.md`
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
- `iOS/workflow/rules/swift-concurrency.md`
- `iOS/workflow/rules/performance/concurrency.md`
- `iOS/workflow/rules/localization.md`
- `iOS/workflow/rules/performance/networking.md`
- `iOS/workflow/rules/accessibility.md`
- `iOS/workflow/rules/ui-design-system.md`
- `iOS/workflow/rules/ui-testing.md`
- `iOS/workflow/rules/ui-test-spec.md`
- `iOS/workflow/rules/simulator.md`
- `iOS/workflow/rules/architecture/mvvm.md`

## Non-goals

- Не создавать экран списка интервью, детали интервью или продолжение интервью.
- Не менять общие продуктовые артефакты, пакет Android, backend или web.
- Не писать production-код, задачи плана или доказательства на этапе propose.
- Не переносить auth-baseline в `MyProfileFeature`; session seam должен быть
  typed и минимальным.

## Existing context

- `iOS/SysDevScen/SysDevScen/ContentView.swift` содержит `RootShellView` с
  тремя tabs и текущей заглушкой `ContentUnavailableView` для profile.
- `iOS/SysDevScen/SysDevScen/RootView.swift` открывает `ContentView()` только
  при `.active` auth state.
- `iOS/AuthFeature/Package.swift` — существующий Swift package с iOS 18.0 и
  StrictConcurrency.
- `iOS/AuthFeature/Sources/AuthFeature/AuthSessionModel.swift` уже содержит
  public `invalidateSession(...)` для возврата в signed-out state.
- `iOS/AuthFeature/Sources/AuthFeature/Data/DefaultAuthAPIClient.swift` умеет
  проверять `/api/profile`, но не содержит history/logout operations.
- `iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj` подключает локальный
  пакет `../AuthFeature` к целевому приложению и задаёт минимальную iOS 26.0.

## Proposed greenfield paths

- `iOS/MyProfileFeature/Package.swift`
- `iOS/MyProfileFeature/Sources/MyProfileFeature/...`
- `iOS/MyProfileFeature/Tests/MyProfileFeatureTests/...`
- подключение package в `iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj`
- минимальная composition в `iOS/SysDevScen/SysDevScen/ContentView.swift`
- создание зависимостей рядом с текущей factory/config в
  `iOS/SysDevScen/SysDevScen/SysDevScenApp.swift`

## Accepted decisions

- Использовать `Swift package` `MyProfileFeature` как isolated physical unit.
- Целевое приложение остаётся владельцем точки входа, жизненного цикла,
  корневой маршрутизации, сборки зависимостей, конфигурации и ресурсов; состояние
  фичи, данных и сети в целевом приложении не размещается.
- Для session seam использовать типизированный contract между app/auth
  composition и `MyProfileFeature`, чтобы профиль мог выполнять session-owned
  requests и инициировать signed-out recovery без доступа к внутренним auth
  details.
- UI строится как SwiftUI MVVM surface: view рендерит state и отправляет typed
  actions, а ViewModel координирует use cases и route/logout event.
- Пагинация истории bounded и cancellable; повторная загрузка не создаёт
  параллельных duplicate requests для одного owner.

## Open questions

None.

## Risks

- Session seam между `AuthFeature` и `MyProfileFeature` может потребовать
  минимального расширения public contract auth package.
- В проекте пока нет `.xcstrings`; реализация должна либо использовать
  обнаруженный механизм генерации строк, либо явно добавить локализационный
  ресурс в package.
- Подключение второго local package в Xcode project должно сохранить
  существующую app shell boundary и не превратить app target во владельца
  поведения feature.
