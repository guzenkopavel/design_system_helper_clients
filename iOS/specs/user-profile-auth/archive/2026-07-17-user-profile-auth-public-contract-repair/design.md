# Design — user-profile-auth / iOS / user-profile-auth

## Current context

Обнаруженный production-контекст iOS состоит из одного application target
`SysDevScen` в проекте `iOS/SysDevScen/SysDevScen.xcodeproj` c тестовыми целями
`SysDevScenTests` и `SysDevScenUITests`. Точка входа —
`iOS/SysDevScen/SysDevScen/SysDevScenApp.swift`: `@main` `SysDevScenApp`
показывает `ContentView` внутри `WindowGroup` без передачи зависимостей.
`iOS/SysDevScen/SysDevScen/ContentView.swift` — доставленная оболочка
`app-shell`: приватный `RootShellView` с `TabView`, закрытым значением
`RootSection` и тремя нейтральными разделами («Кейсы», «Знания», «Профиль»).
Это immutable baseline `iOS/specs/app-shell/SPECIFICATION.md`.

Сетевого кода, storage-кода и хранения секретов в `iOS/SysDevScen` нет; поиск
не нашёл ни одного `Package.swift` внутри `iOS/` — auth-возможность станет
первой физической единицей вне application target. Настройки сборки:
`Xcode 26.5`, `IPHONEOS_DEPLOYMENT_TARGET = 26.5`, `SWIFT_VERSION = 5.0`,
`SWIFT_APPROACHABLE_CONCURRENCY = YES`,
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`; физического `Info.plist` нет
(`GENERATE_INFOPLIST_FILE = YES`), действует default `ATS`. Файлы
`Persistence.swift` и модель `Core Data` остаются техническим следом шаблона и
в новый путь не входят.

Бэкенд доступен по `https://89.125.1.21.nip.io` (внешний параметр окружения) и
предоставляет операции `/api/auth/email-check`, `/api/auth/login`,
`/api/auth/register`, `/api/profile`, серверную cookie-сессию `dsh_session`
(`HttpOnly`, четырнадцать дней), единый конверт ошибок с полями `error.code`,
`error.message`, `error.retryable`, `error.traceId` и ответ `429` с заголовком
`Retry-After`.

Продуктовое поведение принадлежит `specs/product/user-profile-auth/spec.md`
(`READY`, `APPROVED`); этот документ связывает общие идентификаторы с
iOS-решением и не повторяет их наблюдаемые формулировки. Нативное UX-решение
зафиксировано в READY `platform-ux.md` этого package.

## Proposed architecture and boundaries

Auth-возможность выделяется в предлагаемый greenfield `Swift package`
`AuthFeature` по пути `iOS/AuthFeature/` (путь предлагается и до Implement не
существует):

- манифест `iOS/AuthFeature/Package.swift`; точная `swift-tools-version` и
  платформенный минимум подбираются в Plan по найденному тулчейну `Xcode 26.5`
  и deployment target потребителя `iOS 26.5`;
- library-цель `AuthFeature` (`iOS/AuthFeature/Sources/AuthFeature/`) — весь
  код возможности;
- тестовая цель `AuthFeatureTests` (`iOS/AuthFeature/Tests/AuthFeatureTests/`)
  — модульные тесты единицы.

Внутри цели `AuthFeature` применяется Feature-First: папки `Domain/`
(контракты, доменные модели, ошибки, use cases), `Data/` (клиент API, DTO,
Keychain-хранилище секрета) и `Presentation/` (SwiftUI-флоу, view model,
state, actions). Папки — организация исходников одной физической единицы, а не
отдельные modules. Направление зависимостей: `Presentation` зависит от
доменных контрактов, реализации `Data` подставляются композицией; `Domain` не
импортирует UI и транспорт.

Публичный контракт единицы минимален и состоит ровно из:

- `AuthConfiguration` — value type с `apiBaseURL: URL`; throwing-инициализатор
  отклоняет не-`https` адрес, невалидное состояние непредставимо;
- `SessionState` — `enum`: `.checking`, `.signedOut(reason:)` c опциональной
  причиной `SessionEndReason.sessionInvalid`, `.active`;
- `AuthSessionModel` — `@MainActor` `@Observable` владелец состояния сессии:
  `state`, `start()` (однократная проверка сессии при запуске), внутренние
  переходы по успеху флоу и по инвалидации сессии;
- `AuthFlowView` — публичная SwiftUI-поверхность флоу «почта → пароль» с
  инициализатором от `AuthSessionModel`;
- `AuthFeatureFactory` — фабрика композиции: `makeSessionModel(configuration:)`
  собирает live-граф; отдельная точка `makeStubSessionModel(scenario:)` для
  детерминированных UI-тестов.

Все остальные типы (`AuthFlowViewModel`, use cases, клиент, хранилище, DTO)
остаются `internal`. Потребитель ровно один — корневая композиция
`SysDevScen`; она импортирует только перечисленный контракт.

Application target сохраняет только allowlist-обязанности: `SysDevScenApp`
создаёт `AuthConfiguration` из внешнего параметра окружения, получает
`AuthSessionModel` из `AuthFeatureFactory` и в корневой маршрутизации
показывает ровно одну из трёх поверхностей по `SessionState`: спокойное
состояние загрузки (`.checking`), `AuthFlowView` (`.signedOut`) либо
существующую оболочку `ContentView` (`.active`). Реализация auth, сети и
хранения в application target не появляется. Baseline-поведение оболочки не
меняется.

## Data and control flow

Запуск: `SysDevScenApp` собирает граф и вызывает `AuthSessionModel.start()`.
Проверка сессии — use case `CheckSessionUseCase`: читает секрет из
`SessionSecretStore`; при отсутствии секрета сразу `.signedOut(nil)`; при
наличии выполняет персональный запрос `profile`. Успех даёт `.active`; ответ
`401` — очистка секрета и `.signedOut(.sessionInvalid)` с коротким объяснением
на шаге почты; офлайн и прочие сбои дают восстановимое состояние проверки без
мигания формой (наблюдаемый контракт `IOS-REQ-4`).

Флоу авторизации — конечный автомат внутри `AuthFlowViewModel`. Состояние
`AuthFlowState` — одно value-семантическое значение:

- `step`: `.email(EmailStepState)` либо `.password(PasswordStepState)`;
  `PasswordStepState` несёт `mode` (`.login` — заголовок «Вход», `.register` —
  заголовок «Регистрация») и подтверждённую почту, видимую на шаге;
- `phase`: `.idle` либо `.loading` (активный запрос);
- `feedback`: `nil` либо одно из `Feedback.validation(field:message:)`,
  `.invalidCredentials`, `.emailAlreadyRegistered`, `.serverValidation(message:)`,
  `.rateLimited(until:)`, `.offline`, `.sessionEnded`;
- поля ввода: `email` сохраняется при всех переходах и возвратах; `password`
  очищается при ошибке входа, уходе с шага и офлайне.

Типизированные действия `AuthFlowAction`: `.emailChanged`,
`.passwordChanged`, `.submitEmail`, `.submitPassword`,
`.togglePasswordVisibility`, `.returnToEmail`, `.retry`. Переходы:

1. `submitEmail` — локальная валидация (пустота, синтаксис почты) до сети; при
   успехе `CheckEmailUseCase` вызывает `email-check`; результат ветвит шаг
   пароля в `mode` `.login` либо `.register` до показа шага.
2. `submitPassword` — локальная валидация (пустота; при регистрации минимум
   шесть символов) до сети; затем `LogInUseCase` (`login`) либо
   `RegisterAccountUseCase` (`register`). Успех сохраняет секрет через
   `SessionSecretStore` и сообщает `AuthSessionModel` о переходе в `.active`;
   флоу закрывается целиком, корневая маршрутизация заменяет поверхность, и
   навигационный возврат в флоу отсутствует.
3. `returnToEmail` (и равнозначный системный возврат) — отмена активного
   запроса шага, возврат к шагу почты с сохранённой правимой почтой.
4. `retry` — повтор последней операции по явному действию пользователя;
   автоматических повторов нет.

Ошибки `401` (вход), `409`, `422`, `429` c `Retry-After` и офлайн отображаются
в перечисленные `feedback`-состояния согласно `IOS-REQ-7`; состояние
`rateLimited` блокирует отправку до наступления `until` (обратный отсчёт
считается от инжектированного источника времени). Ответ `401` персонального
запроса в любом месте жизни сессии маршрутизируется в
`AuthSessionModel`: очистка секрета, `.signedOut(.sessionInvalid)`
(`IOS-REQ-8`).

## Dependency injection

Композиция собирается в двух точках. Корневая композиция `SysDevScenApp`
создаёт `AuthConfiguration` и один `AuthSessionModel` на жизнь сцены —
scoped-владелец состояния сессии; глобальный изменяемый singleton не вводится.
Внутри package `AuthFeatureFactory` — composition root единицы: создаёт
`DefaultAuthAPIClient` поверх `URLSession`, `KeychainSessionSecretStore`, use
cases и передаёт их через инициализаторы. Контракты (`AuthAPIClient`,
`SessionSecretStore`, протокол источника времени для отсчёта `Retry-After`)
принадлежат `Domain`; реализации — `Data`.

Lifetimes: `AuthSessionModel` и `AuthFlowViewModel` — scoped (сцена и активный
флоу соответственно); клиент и хранилище — stateless `Sendable` значения,
допустимые к переиспользованию; тестовая композиция создаёт всё локально с
fakes без обращения к application singleton. Environment-injection SwiftUI не
переносит бизнес-зависимости: модель передаётся явным параметром
инициализатора. Выбор scripted-заглушки для UI-тестов происходит только в
корневой композиции по явному launch-аргументу; service locator не появляется.

## Error and recovery model

Граница нормализации — `DefaultAuthAPIClient`. Транспортные и серверные сбои
не покидают `Data` в сыром виде: конверт `error.code`, `error.message`,
`error.retryable`, `error.traceId` декодируется в `ErrorEnvelopeResponse` и
отображается в доменную ошибку `AuthError`:

- `401` операции `login` — `.invalidCredentials` (без раскрытия существования
  аккаунта; поле пароля очищается, повтор доступен сразу);
- `409` операции `register` — `.emailAlreadyRegistered` с предложением входа;
- `422` — `.serverValidation(message:)` рядом с формой в том же стиле, что
  локальная валидация;
- `429` — `.rateLimited(retryAfter:)`; заголовок `Retry-After` парсится и как
  секунды, и как HTTP-дата, результат приводится к моменту времени;
- `401` операции `profile` — `.sessionInvalid`, маршрутизируется в очистку
  секрета и возврат на шаг почты;
- сетевые сбои `URLError` (`notConnectedToInternet`, `networkConnectionLost`,
  `cannotConnectToHost`, `timedOut`) — `.offline`, отдельное восстановимое
  состояние с действием повтора;
- прочие статусы и некорректные тела — `.backendFailure(traceId:)`;
  `traceId` сохраняется для диагностики и не показывается в основном тексте.

Отмена (`CancellationError`, `URLError.cancelled`) пробрасывается без
преобразования и никогда не показывается как пользовательская ошибка.
Пользовательские тексты локализуются на presentation-границе; технические
коды в основной текст не попадают. `try?`, silent catch и `fatalError` на
runtime-путях запрещены; каждая async-операция наблюдает свой `throw` и
завершается явным состоянием. Логирование не содержит почту, пароль, секрет и
персональные данные.

## Concurrency model

Изоляция — часть контракта. `AuthSessionModel`, `AuthFlowViewModel` и весь UI
state исполняются на `MainActor` (это совпадает c
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` потребителя; package задаёт
собственные настройки языка в манифесте, точные значения фиксирует Plan по
реальному тулчейну, поведение диагностик не предполагается по версии `Xcode`).
Доменные модели, DTO, ошибки — `Sendable` value types; `DefaultAuthAPIClient`
и `KeychainSessionSecretStore` — stateless `Sendable`. `@unchecked Sendable`,
`nonisolated(unsafe)` и detached tasks не используются.

Политика единственной отправки: view model владеет ровно одной активной
структурированной `Task` на шаг и генерацией запроса (монотонный счётчик).
Активация основного действия при `phase == .loading` игнорируется — второй
сетевой вызов не создаётся (`IOS-AC-15`). Уход с шага, возврат к правке почты
и закрытие флоу вызывают `cancel()` активной задачи; после каждого `await`
результат применяется только при совпадении генерации, поэтому отменённый или
устаревший запрос не меняет видимое состояние задним числом. Ошибка отмены
завершает задачу без изменения `feedback`.

`AuthSessionModel.start()` идемпотентен: повторная активация сцены не создаёт
вторую проверку сессии и второго наблюдателя. Обратный отсчёт `rateLimited`
живёт на `MainActor`, владеет своей задачей и отменяется при уходе состояния.
Continuation-обёртки не требуются: транспорт — нативный async `URLSession`;
блокировки не удерживаются через `await`; CPU-параллелизм не вводится —
операции последовательны по смыслу флоу, fan-out отсутствует, приоритеты не
используются как механизм порядка.

## Security and data handling

Платформенное решение хранения: значение серверного cookie `dsh_session`
хранится только в системном `Keychain` (`kSecClassGenericPassword`,
`kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`, без sharing-групп), что
делает его недоступным другим приложениям и исключает попадание в
незащищённые файлы и `UserDefaults`. Автоматические cookie-хранилища
отключаются: конфигурация сессии `ephemeral`, `httpShouldSetCookies = false`,
`httpCookieAcceptPolicy = .never`, `urlCache = nil` — секрет и персональные
ответы не оседают в дисковых кэшах и `binarycookies`. Значение `dsh_session`
извлекается из заголовков ответа операций `login`/`register` и предъявляется
явным заголовком `Cookie` только в персональных запросах.

Пароль существует только в памяти состояния шага: не сохраняется ни в каком
хранилище, не логируется, очищается после отправки, при ошибке входа, уходе с
шага и офлайне. Недействительный секрет удаляется из `Keychain` до показа
шага почты (`IOS-REQ-8`, `IOS-AC-12`, `IOS-AC-16` общего контракта хранения).
Все запросы уходят только по `https`; default `ATS` не ослабляется, кастомная
trust-политика и обход проверки сертификата запрещены — несовместимый
сертификат окружения является блокером, а не поводом ослабить transport
security. Адрес API — внешний параметр окружения, передаваемый композицией;
литерал адреса в коде package не появляется. Аналитика, трекинг и лишние
entitlement не добавляются.

## Apple SDK considerations

- Networking: фактическая конфигурация — `URLSessionConfiguration.ephemeral` с
  отключёнными cookie и кэшем (см. `Security and data handling`); redirects
  остаются системными; trust — default `ATS` без делегата. Извлечение
  `Set-Cookie` выполняется через API работы с заголовками ответа; точный
  символ и сигнатура (`HTTPCookie.cookies(withResponseHeaderFields:for:)` либо
  прямое чтение `allHeaderFields`) подтверждаются по установленному SDK в
  Implement, а не предполагаются. URL строится структурно через
  `URLComponents`; пользовательский ввод не интерполируется в строку пути.
- `Codable`: стратегии дат/ключей и поведение отсутствующих и `null` полей не
  предполагаются автоматическими — контракт конверта ошибок закрепляется
  fixtures в модульных тестах; `JSONDecoder` создаётся локально на операцию и
  не объявляется thread-safe без документации.
- Keychain: `Security.framework` вызывается синхронно короткими операциями вне
  `MainActor`-блокировок; file protection класс задан явно; корреляция
  диагностики использует `traceId` реального ответа, а не свежий `UUID`.
- SwiftUI lifecycle: реальный вход — `WindowGroup` в `SysDevScenApp`; смена
  корневой поверхности выполняется заменой дерева по `SessionState`, без
  navigation-history; повторные активации сцены идемпотентны, observers не
  дублируются. Внутри флоу — стандартный navigation-контейнер с программным
  переходом к шагу пароля; системный возврат (кнопка и жест) эквивалентен
  явному действию возврата.
- `Liquid Glass`: применяется условно и только на функциональном
  навигационном слое по READY `platform-ux.md`; точный API, availability и
  older-OS/SDK fallback проверяются до использования (см.
  `Platform UX trace and decisions`).
- `build succeeded` не доказывает runtime-корректность: каждое применимое
  SDK-поведение получает unit/simulator evidence в Verify.

## Design-system and accessibility

Слой токенов не обнаружен; единственный визуальный asset — `AccentColor`. Флоу
собирается из `standard components` SwiftUI; роль `soft blue` мапится на
семантический акцент основного действия, фокуса и информационного объяснения
через найденный asset либо подтверждённую точку расширения; литералы цвета,
шрифта и отступов в feature-коде запрещены; новый переиспользуемый primitive
не создаётся без доказанной необходимости.

Каждый контрол несёт русское видимое имя, совпадающее ассистивное имя, роль и
состояние: поля «Почта» и «Пароль», действия «Продолжить», «Войти»,
«Зарегистрироваться», возврат к почте, раскрытие пароля с объявляемым
состоянием. Ошибки, загрузка, ограничение попыток и офлайн объявляются
ассистивно; заблокированность основного действия передаётся семантическим
состоянием, а не только прозрачностью; состояния различимы не только цветом.
Смена шага переводит ассистивный фокус к логическому началу нового шага.
`Dynamic Type` без обрезания (адаптивная вёрстка и прокрутка формы), hit
target не меньше системного минимума, светлое, тёмное и
повышенно-контрастное оформления, `Reduce Transparency`, `Reduce Motion` и
`scrolling legibility` — обязательные швы проверки. Accessibility identifiers
для automation задаются отдельной осью и не подменяют ассистивные имена.

## Migration and rollout

Изменение аддитивно к доставленной оболочке: корневая маршрутизация получает
гейт, сама оболочка не меняется. Миграции данных нет — до изменения секретов
и аккаунтов на устройстве не существовало. Первый запуск после обновления
ведёт себя как запуск без сессии: спокойная загрузка, затем шаг почты. Откат
до релиза — возврат корневой композиции к прямому показу `ContentView` и
удаление единицы из графа; артефакты в `Keychain` при откате не читаются и не
мешают работе. Feature flag не вводится: гейт — утверждённое продуктовое
поведение, а не эксперимент. Contract-совместимость с бэкендом закреплена
фикстурами конверта ошибок; изменение серверного контракта — отдельный цикл.

## Alternatives and trade-offs

- Реализация внутри application target отклонена: modularity v1 даёт strong
  default физической единицы для новой независимой возможности с данными,
  сетью и хранением; размещение в оболочке нарушило бы allowlist и baseline
  `IOS-REQ-1`.
- Три отдельные единицы (сеть, хранение, флоу) отклонены: у транспорта и
  секрета ровно один потребитель внутри возможности, независимое владение не
  доказано; дробление по горизонтальным уровням дало бы только служебные
  публичные границы (over-modularization).
- Автоматическое cookie-хранилище `HTTPCookieStorage` отклонено: его
  персистентность не удовлетворяет обязательству недоступности другим
  приложениям и наблюдаемой очистки (`IOS-REQ-9`); явное владение секретом в
  `Keychain` проще проверяется инспекцией хранилища.
- Готовый сетевой framework отклонён: четыре операции покрываются нативным
  async `URLSession` без внешней зависимости; политика версий зависимостей не
  затрагивается.
- Автоматический retry транспорта отклонён: `login`/`register` не
  идемпотентны, повтор — только явное действие пользователя; ограничение
  `429` соблюдается клиентски.
- Экранная маршрутизация через navigation-history для гейта отклонена: замена
  корневого дерева по `SessionState` делает возврат в флоу после успеха
  невозможным по построению (`IOS-REQ-6`).

## Modularity decision

- Outcome: isolated
- Capability triggers: independent-feature=yes; domain-data=yes; network=yes; persistence=yes; reusable-ui=no; consumers=1; independent-ownership=yes
- Physical boundaries: Предлагаемый новый Swift package AuthFeature в iOS/AuthFeature с library Swift package target AuthFeature и тестовой Swift package target AuthFeatureTests.
- Public contracts and dependency direction: Минимальный публичный контракт единицы — AuthConfiguration, SessionState, AuthSessionModel, AuthFlowView и AuthFeatureFactory; единственный потребитель импортирует только этот контракт, направление зависимостей ацикличное — от корневой композиции к единице, обратных зависимостей и знания о потребителе внутри единицы нет.
- App-shell responsibilities: entry-points, lifecycle, root-routing, dependency-wiring, platform-configuration, target-resources
- App-shell capability ownership: none
- Repository evidence: iOS/SysDevScen/SysDevScen/SysDevScenApp.swift; iOS/SysDevScen/SysDevScen/ContentView.swift; iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj; iOS
- Rationale and trade-offs: Связная auth-возможность объединяет флоу, сетевого клиента и хранение секрета с независимым владением и собственными тестами; в каталоге iOS нет ни одного манифеста Package.swift, единица создаётся впервые, и выделение улучшает владение, тестируемость, видимость публичного контракта и переиспользуемость проверок; ценой являются манифест и явная граница composition, что дешевле размывания ответственности корневой композиции.
- Migration boundary and trigger: Типизированные протокольные швы AuthAPIClient и SessionSecretStore уже отделяют транспорт и хранилище внутри единицы; при появлении второго потребителя auth-контракта или доказанной переиспользуемой возможности общая часть выделяется отдельным архитектурным решением с собственным публичным контрактом.
- Over-modularization check: Единица не дробится на отдельные физические части сети, хранения и представления — у транспорта и секрета один владелец и один потребитель внутри возможности, поэтому дробление по горизонтальным уровням или по папкам дало бы только служебные публичные границы и стоимость сборки без пользы для владения, тестируемости и видимости.
- Boundary guard verdict: PASS

## Applied engineering scopes

- application: `iOS/workflow/rules/app-development.md` закрепляет найденный вход `WindowGroup`, идемпотентные активации сцены, отсутствие тяжёлой работы на старте (проверка сессии асинхронна за спокойным состоянием загрузки) и запрет чувствительной конфигурации в source; `iOS/workflow/rules/ios-pitfalls.md` применён к networking (конфигурация сессии, cookie, trust), `Codable`-фикстурам, `Keychain` file protection и корреляции по `traceId`; `iOS/workflow/rules/architecture/feature-first.md` даёт вертикальную единицу с направлением `Presentation` к доменным контрактам и изоляцией транспорта и хранилища от публичного API; `iOS/workflow/rules/architecture/dependency-injection.md` — композиция в двух явных корнях, ограниченные времена жизни, без глобального одиночки и без скрытого поиска сервисов; `iOS/workflow/rules/architecture/use-cases.md` — четыре use case c явными контрактами, доменными ошибками и политикой идемпотентности (повтор только явным действием); `iOS/workflow/rules/architecture/error-handling.md` — нормализация конверта на границе клиента, отмена не маскируется, silent catch запрещён; `iOS/workflow/rules/architecture/naming.md` — протоколы по способности (`AuthAPIClient`, `SessionSecretStore`), реализация `Default*`/`Keychain*`, use cases `VerbNounUseCase`, presentation `AuthFlowView`/`AuthFlowViewModel`/`AuthFlowState`/`AuthFlowAction`; `iOS/workflow/rules/architecture/legacy.md` — шаблонные `Persistence.swift` и `Core Data` остаются нетронутым техническим следом, новый код в deprecated-ветку не добавляется; `iOS/workflow/rules/architecture/types-clean-code.md` — value-типы состояний, `enum` c associated data вместо несогласованных optionals, throwing-инициализатор `AuthConfiguration`; `iOS/workflow/rules/unit-testing.md` — детерминированные тесты переходов, инжектированные fakes, фиктивный источник времени для `Retry-After`.
- concurrency: `iOS/workflow/rules/swift-concurrency.md` реализован в секции `Concurrency model` — `MainActor` для UI state, структурированные задачи с владельцем и триггером отмены, перепроверка генерации после каждого `await`, `Sendable` value-границы, запрет `@unchecked Sendable` и detached tasks; фактические language mode и диагностики package фиксируются в Plan по реальным настройкам; `iOS/workflow/rules/performance/concurrency.md` — последовательный DAG операций флоу без fan-out, отсутствие блокировок через `await`, приоритеты не используются как механизм порядка, параллелизм не вводится без измерения.
- networking: `iOS/workflow/rules/performance/networking.md` — политика кэша явная (`ephemeral`, `urlCache = nil`, персональные данные не кэшируются), дубликаты запросов исключены единственной активной задачей и генерацией, автоматический retry отсутствует для неидемпотентных операций и подсказка сервера `Retry-After` соблюдается, URL строится через `URLComponents` c корректным encoding; вариативность живого бэкенда не превращается в детерминированный `PASS` — недоступная среда даёт `UNKNOWN` c диагностикой.
- package: `iOS/workflow/rules/package-development.md` — предлагаемая единица `AuthFeature` с минимальным публичным продуктом, `internal`-реализациями, ацикличными зависимостями от политики к деталям, собственными модульными тестами без опоры на application singleton, bundle layout и signing (реальный `Keychain` проверяется интеграционно на уровне потребителя); манифест, подключение потребителя, публичные тесты API и сборка потребителя фиксируются в Plan; `iOS/workflow/rules/architecture/dependency-injection.md` — фабрика композиции публикует только необходимую сборку; `iOS/workflow/rules/architecture/error-handling.md` — доменная категория ошибок стабильна на публичной границе; `iOS/workflow/rules/architecture/naming.md` — имена продукта и целей следуют возможности, а не слою; `iOS/workflow/rules/architecture/types-clean-code.md` — публичная поверхность выражена узкими типами; `iOS/workflow/rules/unit-testing.md` — тесты единицы детерминированы и независимы от порядка.
- ui: `iOS/workflow/rules/architecture/mvvm.md` — один source of truth `AuthFlowState`, typed actions, политика эффекта «игнорировать при загрузке, отменять при уходе», маршрут успеха как типизированное событие в `AuthSessionModel`; `iOS/workflow/rules/accessibility.md` — совпадение имён, объявления состояний, управление фокусом, `Dynamic Type`, hit targets, реальные VoiceOver-проверки на симуляторе; `iOS/workflow/rules/ui-design-system.md` — semantic roles, `standard components`, найденный `AccentColor`, запрет выдуманных токенов и кастомного glass, conditional `Liquid Glass` по `platform-ux.md`; `iOS/workflow/rules/ui-testing.md` — сценарии от observable state, приоритет accessibility identifier, контролируемые данные через scripted-заглушку по launch-аргументу вместо живой сети; `iOS/workflow/rules/ui-test-spec.md` — разложение каждого AC на шаги, действия и assertions живёт в `verification.md` и plan tasks без дублирования продуктовых сценариев; `iOS/workflow/rules/simulator.md` — runtime, устройства, reset, appearance и диагностика обнаруживаются до запуска, недоступное устройство даёт `UNKNOWN`.

Базовые lifecycle-правила из `applicable_rule_files`, не входящие в
scope-профили, отображаются на решения так:

| Правило | Архитектурное применение |
|---|---|
| `workflow/rules/specification-layers.md` | Документ не копирует наблюдаемый продуктовый текст и ссылается на общие идентификаторы |
| `workflow/rules/artifact-language.md` | Русская авторская проза с точными идентификаторами и путями без перевода |
| `workflow/rules/system-design.md` | Standard-набор тем применён в секции обзора системного дизайна |
| `workflow/rules/system-design/modularity.md` | Структурированное решение `isolated` с machine schema и evidence |
| `iOS/workflow/rules/architecture.md` | Инварианты направлений зависимостей и минимальной публичной поверхности соблюдены во всех секциях |
| `iOS/workflow/rules/package-development.md` | Правила физической единицы применены в scope `package` и решении о границе |
| `workflow/rules/coding-standards.md` | Реализация обязана следовать найденному стилю потребителя и не вводить попутный рефакторинг |
| `workflow/rules/tdd-first.md` | План обязан вести вертикальные слайсы через RED и GREEN от валидации к сетевым состояниям |
| `workflow/rules/test-execution.md` | Нетривиальные проверки исполняются с конечным watchdog и сохранённым выводом |
| `workflow/rules/verification-matrix.md` | Матрица методов уже разложена в `verification.md` по слоям unit, UI, integration, architecture |
| `workflow/rules/code-comments.md` | Комментарии объясняют неочевидные решения (генерация запроса, политика cookie), а не пересказывают код |
| `iOS/workflow/rules/swift-style.md` | Свифт-стиль применяется в Implement по найденной конфигурации проекта |
| `workflow/rules/verification-evidence.md` | Каждая проверка получает отдельное свежее evidence в package до `PASS` |

## Platform UX trace and decisions

READY `platform-ux.md` этого package — источник нативного UX; его продуктовый
источник — `specs/product/user-profile-auth/ux.md`. Архитектура инкорпорирует
его решения так:

- Три корневые поверхности (определение сессии, флоу, оболочка) реализованы
  заменой корневого дерева по `SessionState` — ровно одна поверхность видима,
  переход к результату происходит один раз, мигание формой исключено
  состоянием `.checking`.
- Линейный флоу в одном нативном navigation-контейнере с программным
  переходом: заголовок «Вход»/«Регистрация» вычисляется до показа шага пароля
  (результат `CheckEmailUseCase` входит в `PasswordStepState.mode`); системный
  возврат и явное действие возврата сведены к одному action `.returnToEmail`.
- Карта состояний UX (`default`, `focused`, `loading`, `error`, `empty`,
  `rate limit`, `offline`) взаимно однозначно ложится на `phase` и `feedback`
  в `AuthFlowState`; очистка пароля после ошибки входа и сохранение почты в
  офлайне — инварианты состояния, а не побочные эффекты view.
- `standard components`, семантические роли `soft blue`, поведение клавиатуры
  почты и раскрытие пароля закреплены в `Presentation` без кастомных контролов
  и литералов оформления; клавиатурное действие «продолжить» диспатчит тот же
  action, что и основная кнопка, и подчиняется той же блокировке.
- Conditional `Liquid Glass` ограничен функциональным навигационным слоем:
  реализация проверяет точный символ SDK и availability до использования;
  `content background` не становится glass; на `iOS 18.6` и при недоступности
  API действует наблюдаемый fallback — стандартное непрозрачное семантическое
  оформление с тем же поведением; `Reduce Transparency` и `Reduce Motion`
  используют системные адаптации без самодельной имитации.
- Ассистивные обязательства UX (объявления, перевод фокуса к началу шага,
  совпадение имён, `Dynamic Type`, `scrolling legibility`) — проверяемые швы
  `Presentation` и входят в verification seams, а не остаются пожеланиями.

## System-design review

- Ландшафт: primary — гейт запуска, двухшаговый флоу, клиент четырёх операций,
  хранение секрета; secondary — доставленная оболочка (не меняется), шаблонный
  `Core Data` (не используется), бэкенд как внешняя система с фиксированным
  контрактом. Существующий layout отделён от greenfield: единица
  `iOS/AuthFeature` и все её пути — предлагаемые.
- Вторичные требования: безопасность хранения, офлайн, ограничение попыток,
  ассистивность и appearance учтены как явные состояния и швы проверки, а не
  как happy-path дополнение.
- Mobile challenges: нестабильная сеть решается явными состояниями `offline` и
  восстановимым повтором; жизненный цикл процесса — идемпотентной проверкой
  сессии и хранением секрета вне памяти; вариативность окружения бэкенда —
  статусом `UNKNOWN` вместо предположений.
- Труднообратимые решения: физическая граница единицы, публичный контракт из
  пяти типов, платформенное решение хранения секрета в `Keychain` и запрет
  ослабления `ATS` зафиксированы здесь; они меняются только новым
  architecture-решением, а не в ходе Implement.
- Гейт дизайна: verdict read-only boundary guard возвращается владельцу этого
  документа; без `PASS` гейт `design_gate` не проходит.

## Traceability to platform contract

| Contract ID | Архитектурное решение |
|---|---|
| IOS-REQ-1 | Корневая композиция владеет только allowlist-обязанностями; auth подключается как внешняя единица (`Proposed architecture and boundaries`) |
| IOS-REQ-2 | Нативные `standard components`, ассистивные имена и объявления в `Design-system and accessibility` |
| IOS-REQ-3 | Шаблонный `Core Data` и исключённые границы не входят в новый путь (`Current context`, `Migration and rollout`) |
| IOS-REQ-4 | Состояние `.checking` и `CheckSessionUseCase` c маршрутизацией трёх поверхностей (`Data and control flow`) |
| IOS-REQ-5 | Автомат шагов c ветвлением `mode` до показа шага пароля и возвратом c сохранённой почтой |
| IOS-REQ-6 | Замена корневого дерева по `SessionState` делает возврат в флоу невозможным по построению |
| IOS-REQ-7 | Перечислимые `feedback`-состояния c локальной валидацией до сети и отображением серверных ошибок |
| IOS-REQ-8 | Маршрут `.sessionInvalid`: очистка секрета до показа шага почты (`Error and recovery model`) |
| IOS-REQ-9 | Секрет в `Keychain`, пароль только в памяти, отключённые cookie-хранилища (`Security and data handling`) |
| IOS-REQ-10 | `DefaultAuthAPIClient` c четырьмя операциями, конвертом ошибок и явным заголовком `Cookie` |
| IOS-REQ-11 | Единственная активная задача, генерация запроса, отмена при уходе (`Concurrency model`) |
| IOS-REQ-12 | Решение `isolated`: единица `AuthFeature` c минимальным контрактом (`Modularity decision`) |
| IOS-REQ-13 | Паритет текстов и шагов через словарь состояний и `Platform UX trace and decisions` |
| IOS-AC-1 | Статическая проверка владения обеспечена явной границей композиции и публичного контракта |
| IOS-AC-2 | Ассистивные швы `Presentation`: имена, объявления, фокус, оформления |
| IOS-AC-3 | Отсутствие шаблона и лишних границ проверяемо по составу нового пути |
| IOS-AC-4 | Наблюдаемая последовательность «загрузка, затем шаг почты» из состояния `.checking` |
| IOS-AC-5 | Персистентность секрета в `Keychain` даёт вход без формы при перезапуске |
| IOS-AC-6 | Ветвление заголовков и сохранение почты — инварианты `AuthFlowState` |
| IOS-AC-7 | Успех обоих use case завершает флоу одним событием в `AuthSessionModel` |
| IOS-AC-8 | Локальная валидация выполняется до вызова клиента и покрывается модульными тестами |
| IOS-AC-9 | Отображение `401`, `409`, `422` в доменные ошибки детерминировано и тестируемо fixtures |
| IOS-AC-10 | Состояние `rateLimited(until:)` c инжектированным временем блокирует отправку до срока |
| IOS-AC-11 | Отображение `URLError` в `.offline` c повтором и сохранённой почтой |
| IOS-AC-12 | Сценарий инвалидации: очистка секрета и возврат проверяются интеграционно |
| IOS-AC-13 | Инспекция хранилища подтверждает изоляцию секрета и отсутствие пароля |
| IOS-AC-14 | Модульные тесты клиента c подменой транспорта: `https`, конверт, `Cookie`, маршрут `401` |
| IOS-AC-15 | Тесты конкурентности: единственная отправка, отмена, отсутствие поздних мутаций |
| IOS-AC-16 | Граф зависимостей, публичный API и тесты единицы — предмет boundary-проверки |
| IOS-AC-17 | Сквозной проход по scripted-заглушке воспроизводит шаги и тексты общего контракта |

## Platform verification gates

- Гейт границы: read-only `ios-package-boundary-guard` обязан вернуть `PASS`
  для решения `isolated`; missing или `BLOCK` возвращает design владельцу и
  блокирует `design_gate`.
- Scope-гейты adapter: `application boundary` (владение композицией);
  `cancellation` и `isolation` (конкурентность); `cache policy` и
  `retry policy` (сетевой слой); `package consumer`, `consumer integration`,
  `package build`, `public contract`, `dependency graph`, `app-shell wiring`
  (физическая единица); `simulator`, `accessibility`, `design-system` (UI).
- Нативные UX-обязательства: девять `NATIVE-*` записей `verification.md`
  закрываются отдельными наблюдениями, включая `older-OS/SDK fallback` на
  доступном симуляторе `iOS 18.6` либо честный `UNKNOWN`.
- Дисциплина исполнения: нетривиальные проверки идут с конечным watchdog;
  живой бэкенд при недоступности даёт `UNKNOWN` c диагностикой, а не `PASS`;
  сборка не считается доказательством runtime-поведения.

## Verification strategy

Модульные тесты единицы `AuthFeatureTests` (детерминированные, c локальными
fakes): локальная валидация трёх случаев без сетевого вызова; отображение
конверта ошибок и статусов `401`, `409`, `422`, `429`, офлайна в доменные
ошибки и `feedback`; парсинг `Retry-After` в обоих форматах; переходы
автомата шагов, сохранение почты, очистка пароля; политика единственной
отправки, отмена при уходе и отсутствие поздних мутаций по генерации;
извлечение и предъявление `dsh_session` на подменённом транспорте
(`URLProtocol`-заглушка); контракт `SessionSecretStore` на подменном хранилище в памяти.

Тесты потребителя: `SysDevScenTests` — маршрутизация трёх поверхностей по
`SessionState` и владение композицией; `SysDevScenUITests` — сценарии гейта,
ветвления, возврата, состояний `429` и офлайна, успешного входа и регистрации
на scripted-заглушке, включённой launch-аргументом в корневой композиции;
живой бэкенд в UI-тесты не входит. Интеграционные проверки на симуляторе:
перезапуск в пределах жизни сессии, возврат по `401` c инспекцией хранилища
(секрет удалён, пароль не сохранён). Ассистивные, appearance- и
`Liquid Glass`/fallback-наблюдения выполняются по сценариям
`platform-ux.md`. Полный mapping контрактов и методов остаётся в
`verification.md`; все статусы в Propose — `pending`, свежие evidence создаёт
только фаза `verify`.
