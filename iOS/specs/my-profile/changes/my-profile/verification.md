# Verification — my-profile / iOS / my-profile

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

| Contract ID | Layer | Method | Evidence path | Status |
|---|---|---|---|---|
| REQ-1 | shared contract | Проверить runtime-сценарий вкладки профиля на iOS и визуальную иерархию. | expected evidence before verify | pending |
| REQ-2 | shared contract | Проверить тесты пакета для полного подсчёта истории. | expected evidence before verify | pending |
| REQ-3 | shared contract | Проверить UI-состояние для доступного действия при счётчике больше нуля. | expected evidence before verify | pending |
| REQ-4 | shared contract | Проверить событие сообщения и отсутствие навигации после нажатия. | expected evidence before verify | pending |
| REQ-5 | shared contract | Проверить недоступное состояние при пустой истории. | expected evidence before verify | pending |
| REQ-6 | shared contract | Проверить маршрут выхода к пустому шагу ввода email. | expected evidence before verify | pending |
| REQ-7 | shared contract | Проверить состояния ошибки, offline и восстановления недействительной сессии. | expected evidence before verify | pending |
| REQ-8 | shared contract | Проверить отсутствие iOS-only fork относительно общего поведения. | expected evidence before verify | pending |
| REQ-9 | shared contract | Проверить VoiceOver labels, признаки traits и announcements для профильного экрана. | expected evidence before verify | pending |
| REQ-10 | shared contract | Проверить Dynamic Type, варианты appearances, contrast и non-color cues для всех состояний. | expected evidence before verify | pending |
| AC-1 | shared acceptance | Сценарий симулятора проверяет layout содержимого вкладки профиля. | expected evidence before verify | pending |
| AC-2 | shared acceptance | Unit-тест проверяет догрузку страниц до завершения пагинации. | expected evidence before verify | pending |
| AC-3 | shared acceptance | State-тест проверяет доступное действие при счётчике больше нуля. | expected evidence before verify | pending |
| AC-4 | shared acceptance | UI/state-тест проверяет сообщение «Интервью: N». | expected evidence before verify | pending |
| AC-5 | shared acceptance | UI-тест проверяет отсутствие навигации после сообщения. | expected evidence before verify | pending |
| AC-6 | shared acceptance | UI/state-тест проверяет видимое недоступное действие при нулевом счётчике. | expected evidence before verify | pending |
| AC-7 | shared acceptance | UI-сценарий проверяет возврат выхода к пустому шагу ввода email. | expected evidence before verify | pending |
| AC-8 | shared acceptance | UI/state-тест проверяет очистку профильного отображения после выхода. | expected evidence before verify | pending |
| AC-9 | shared acceptance | State-тест проверяет доступность действий при ошибке истории или offline. | expected evidence before verify | pending |
| AC-10 | shared acceptance | State/UI-тест проверяет восстановление недействительной сессии. | expected evidence before verify | pending |
| AC-11 | shared acceptance | State-тест проверяет восстановление после сбоя выхода. | expected evidence before verify | pending |
| AC-12 | shared acceptance | Контрактная проверка сверяет iOS-поведение с общей parity. | expected evidence before verify | pending |
| AC-13 | shared acceptance | Accessibility-аудит проверяет email и labels действий в блоке профиля. | expected evidence before verify | pending |
| AC-14 | shared acceptance | Accessibility-аудит проверяет `announcements` для недоступного состояния, `feedback` и `logout loading`. | expected evidence before verify | pending |
| AC-15 | shared acceptance | Сценарий Dynamic Type проверяет отсутствие clipping. | expected evidence before verify | pending |
| AC-16 | shared acceptance | Сценарий light and dark проверяет readability. | expected evidence before verify | pending |
| AC-17 | shared acceptance | Сценарий increased contrast проверяет readability и признаки state cues для действий. | expected evidence before verify | pending |
| AC-18 | shared acceptance | UI-сценарий проверяет non-color cues для состояний. | expected evidence before verify | pending |
| IOS-REQ-1 | platform contract | Проверить подключение пакета, публичную фабрику и allowlist оболочки приложения. | expected evidence before verify | pending |
| IOS-REQ-2 | platform contract | Проверить построение запросов, передачу сессии и тесты маппинга ошибок. | expected evidence before verify | pending |
| IOS-REQ-3 | platform contract | Проверить рендеринг состояния SwiftUI и переходы действий. | expected evidence before verify | pending |
| IOS-REQ-4 | platform contract | Проверить интеграцию маршрута выхода и недействительной сессии. | expected evidence before verify | pending |
| IOS-REQ-5 | platform contract | Проверить нативные UX-обязательства из `platform-ux.md`. | expected evidence before verify | pending |
| IOS-REQ-6 | platform contract | Проверить `MainActor`, отмену, режим единственного запроса и тесты пагинации. | expected evidence before verify | pending |
| IOS-AC-1 | platform acceptance | Сборка потребителя и инспекция границы пакета. | expected evidence before verify | pending |
| IOS-AC-2 | platform acceptance | Проверка production diff на изменения только композиции приложения. | expected evidence before verify | pending |
| IOS-AC-3 | platform acceptance | Фокусные тесты контрактов API. | expected evidence before verify | pending |
| IOS-AC-4 | platform acceptance | Фокусные тесты маппинга ошибок и восстановления. | expected evidence before verify | pending |
| IOS-AC-5 | platform acceptance | Сценарий симулятора для содержимого профиля. | expected evidence before verify | pending |
| IOS-AC-6 | platform acceptance | Сценарий симулятора для выхода. | expected evidence before verify | pending |
| IOS-AC-7 | platform acceptance | Записи проверки нативного UX. | expected evidence before verify | pending |
| IOS-AC-8 | platform acceptance | Тесты пагинации и отмены. | expected evidence before verify | pending |

## Revalidated engineering scopes and exact verify rules

Области остаются `application`, `concurrency`, `localization`, `networking`,
`package`, `ui`. Verify должен использовать точный набор правил жизненного цикла
из `meta.json`, включая базовую modularity и package rule, а также выбранные
правила iOS для границы приложения, Swift concurrency, localization, networking,
accessibility, design-system, UI testing, simulator и MVVM.

## Derived method matrix

- Тесты пакета: пагинация, построение запросов, маппинг ошибок, переходы
  состояния ViewModel, отмена и политика защиты от дублирующих запросов.
- Интеграция потребителя: сборка Xcode подтверждает, что `SysDevScen`
  потребляет публичный продукт `MyProfileFeature`.
- Runtime UI: содержимое вкладки профиля, сообщение, недоступное состояние и
  маршрут выхода.
- Accessibility: порядок VoiceOver, `labels`, `traits`, `announcements` и целевые зоны `hit targets` для интерактивных элементов.
- Appearance: светлый режим light, тёмный режим dark, increased contrast и Dynamic Type.
- Проверка границы: целевое приложение остаётся только композицией.

## Build and integration

Команды сборки, schemes и destinations должны быть обнаружены на этапе Plan.
Кандидатные доказательства должны включать тесты пакета `MyProfileFeature`,
сборку целевого приложения с подключением пакета и фокусные UI-тесты для
профильного потока. Живой API не требуется для детерминированного PASS;
предпочтительны fixture или stub-состояния.

## Platform runtime evidence

Доказательства симулятора должны фиксировать device/runtime, аргументы запуска
приложения или источник fixture, выбранную вкладку, видимый email, состояние
действия, сообщение со счётчиком и маршрут выхода. Сбои runner дают UNKNOWN с
диагностикой, а не PASS.

## Accessibility and design-system

Верификация должна включать VoiceOver semantics или accessibility hierarchy,
Dynamic Type с длинным email, hit targets 44×44pt, доказательства light/dark/
increased contrast, недоступное состояние не только цветом и сценарии Reduce
Transparency / Reduce Motion для fallback Liquid Glass.

## Native UX verification

Нативные сценарии приходят из `platform-ux.md` и должны быть записаны как
package-relative JSON observation records внутри `evidence/` на этапе verify.
Каждое обязательство хранит отдельные доказательство и статус.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | pending | pending |
| NATIVE-LIGHT | pending | pending |
| NATIVE-DARK | pending | pending |
| NATIVE-INCREASED-CONTRAST | pending | pending |
| NATIVE-ASSISTIVE-SEMANTICS | pending | pending |
| NATIVE-TEXT-SCALING | pending | pending |
| NATIVE-MOTION | pending | pending |
| NATIVE-DEVICE-ADAPTATION | pending | pending |
| NATIVE-AVAILABILITY-FALLBACK | pending | pending |

## Unverified risks

- Стык сессии с `AuthFeature` может потребовать аккуратного расширения публичного API.
- Выбор ресурса локализации ещё не реализован и должен быть запланирован.
- Подключение второго локального пакета Swift в проект Xcode должно быть
  подтверждено сборкой потребителя и проверкой diff проекта.
