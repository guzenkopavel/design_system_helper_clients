# Proposal — user-profile-auth / iOS / user-profile-auth

## Intake

- Change type: `product-backed`
- Shared product spec: `specs/product/user-profile-auth/spec.md`
- Product status / approval: `READY` / `APPROVED`
- Product impact assessment: `PRESENT`
- Evidence: общий контракт `specs/product/user-profile-auth/spec.md` имеет
  статус `READY` и явное `Product approval: APPROVED` от владельца продукта
  `Pavel Guzenko (product owner)`; receipt
  `specs/product/user-profile-auth/review-verdicts.json` на отпечатке
  `sha256:a47ea1ee08df04e5ceb08f10cfee5e5aa8442b2392a6657f7b76360275da2a6e`
  фиксирует `PASS` всех шести линз продуктового ревью.
- Tier: `standard`

## Goal

Реализовать на iOS утверждённый общий email-first флоу авторизации: гейт всего
приложения за входом, двухшаговый флоу «почта → пароль», немедленный переход в
доставленную оболочку `app-shell` после успеха и сохранение серверной сессии
между запусками на срок её жизни.

## Scope

В объём входят: проверка состояния сессии при запуске со спокойным состоянием
загрузки; экран авторизации с шагом почты, ветвлением «Вход»/«Регистрация» и
шагом пароля; наблюдаемые состояния валидации, серверных ошибок, ограничения
попыток и офлайна; защищённое хранение сессионного секрета на устройстве;
клиент к существующему API бэкенда (`email-check`, `login`, `register`,
`profile`); выделение новой auth-возможности в отдельную физическую единицу и
подключение её к корневой композиции `SysDevScenApp`. Baseline-поведение
оболочки `app-shell` сохраняется без изменений, кроме гейтинга запуска.

## Engineering scope selection

- Selected scopes: `application`, `concurrency`, `networking`, `package`, `ui`.
- Evidence for each scope:
  - `ui` — общий `specs/product/user-profile-auth/ux.md` требует новый экран
    авторизации с шагами, состояниями и ассистивной семантикой; это новая
    видимая SwiftUI-поверхность.
  - `application` — гейт запуска меняет корневую композицию приложения в
    найденных `iOS/SysDevScen/SysDevScen/SysDevScenApp.swift` и
    `iOS/SysDevScen/SysDevScen/ContentView.swift`: до входа показывается только
    флоу авторизации, после — доставленная оболочка.
  - `networking` — нужен клиент к API бэкенда (`email-check`, `login`,
    `register`, `profile`); поиск не нашёл ни одного сетевого кода
    (`URLSession` и аналогов) в `iOS/SysDevScen`, слой создаётся с нуля.
  - `concurrency` — флоу асинхронный: проверка сессии при запуске, сетевые
    запросы с блокировкой повторной отправки, отмена запроса при уходе с шага;
    требования `Loading`-состояний общего контракта проверяемы только при
    корректной модели конкурентности.
  - `package` — modularity v1: новая связная auth-возможность (флоу, сеть,
    хранение сессии) по strong default обязана получить физическую единицу
    (`Swift package`); в `iOS/` сейчас нет ни одного `Package.swift`, единица
    создаётся впервые.
- Considered but not selected:
  - `localization` — тексты фиксированы на русском текущим контрактом
    (`REQ-9`, раздел `Localization` общей спеки); отдельной локализационной
    работы нет.
  - `startup`, `performance`, `memory`, `rendering` — при запуске добавляется
    только лёгкая проверка сессии; отдельный измеримый бюджет
    запуска/памяти/рендеринга этим изменением не вводится.
  - `xcode`, `simulator`, `delivery`, `developer-experience` — изменений
    тулчейна, конфигурации сборки и дистрибуции нет; runtime-проверки
    интерфейса приходят из выбранного `ui`.

## Applicable rule files

Точный lifecycle union базовых профилей фаз `propose`, `plan`, `implement`,
`verify` и выбранных scopes из `iOS/workflow/platform-contract.json`:

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
- `iOS/workflow/rules/swift-concurrency.md`
- `iOS/workflow/rules/performance/concurrency.md`
- `iOS/workflow/rules/performance/networking.md`
- `iOS/workflow/rules/accessibility.md`
- `iOS/workflow/rules/ui-design-system.md`
- `iOS/workflow/rules/ui-testing.md`
- `iOS/workflow/rules/ui-test-spec.md`
- `iOS/workflow/rules/simulator.md`
- `iOS/workflow/rules/architecture/mvvm.md`

## Non-goals

Не входят: пользовательский выход и наполнение раздела «Профиль», сброс
пароля, подтверждение почты, внешние провайдеры, продление сессии,
биометрический вход и PIN-код, офлайн-кэш контента, аналитика, реальное
содержимое разделов оболочки, изменения бэкенда и веба, изменения Android.
План, production-код и commit в этой фазе не создаются.

## Existing context

Найденный текущий контекст iOS:

- корневая композиция `iOS/SysDevScen/SysDevScen/SysDevScenApp.swift` и
  доставленная оболочка `iOS/SysDevScen/SysDevScen/ContentView.swift` —
  immutable baseline `iOS/specs/app-shell/SPECIFICATION.md` (контракт
  `IOS-REQ-1`–`IOS-REQ-3` остаётся в силе);
- проект   `Xcode 26.5 (17F42)`, цель развёртывания `iOS 26.5`,
  `SWIFT_VERSION 5.0`, режим мягкой конкурентности; схема `SysDevScen`,
  цели `SysDevScen`, `SysDevScenTests`, `SysDevScenUITests`; доступны
  симуляторы `iOS 26.5` и `iOS 18.6`;
- `GENERATE_INFOPLIST_FILE=YES` — физического `Info.plist` нет; действует
  default `ATS`;
- сетевого и storage-кода в `iOS/SysDevScen` нет; `Swift package` в `iOS/`
  отсутствует — networking, хранение сессии и auth-единица создаются с нуля;
- бэкенд доступен по `https://89.125.1.21.nip.io`; адрес — внешний параметр
  окружения, а не продуктовое или платформенное решение.

## Proposed greenfield paths

Предлагается новая физическая единица auth-возможности — `Swift package`
внутри `iOS/` с собственными модульными тестами — и её подключение к корневой
композиции приложения. Точные пути, имя package и структура целей выбираются
владельцем `design.md`; этот документ не объявляет их существующими заранее.

## Accepted decisions

Общий контракт остаётся единственным источником продуктового поведения;
платформенный пакет добавляет только iOS-интеграцию, владение и контекст
проверки. Гейт запуска реализуется в корневой композиции приложения, а сама
auth-возможность выносится за границу application target по modularity v1.
Хранение сессионного секрета описывается наблюдаемыми обязательствами
(недоступность другим приложениям, очистка недействительного секрета,
отсутствие сохранённого пароля) без выбора конкретного API за
`architecture-designer`. Визуальную адаптацию iOS закрепит conditional
`platform-ux.md` (Liquid Glass) до architecture.

## Open questions

Нет открытых вопросов.

## Risks

Сетевой и storage-слой создаются с нуля: до Implement нельзя утверждать
поведение реального бэкенда сверх зафиксированного контракта (единый формат
ошибок, ограничение 5 попыток на 15 минут, cookie-сессия 14 дней). Проверка
состояний `429` c временем повтора и офлайна потребует управляемых условий на
simulator. Default `ATS` и защищённый канал обязательны: самоподписанные или
нестандартные сертификаты окружения стали бы блокером, который нельзя обходить
ослаблением transport security без явного решения. До READY `platform-ux.md`
нельзя утверждать нативный вид, appearance-варианты и fallback для старых
OS/SDK.
