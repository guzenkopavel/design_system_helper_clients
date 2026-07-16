# iOS verification — user-profile-auth

Кандидат до фазы `verify`: все статусы — `pending`, evidence-колонка описывает
ожидаемое будущее обязательство. `verify` заменит описания конкретными
package-relative путями `evidence/...` и точными статусами `PASS`, `FAIL` или
`UNKNOWN`. Каждая атомарная AC и `Verification dimension` получает отдельную
row и отдельное наблюдаемое evidence; одна row не агрегирует независимые
dimensions.

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

Ожидаемые доказательства: направленный граф от application target к новой
auth-единице (`Swift package`), минимальный публичный контракт единицы,
собственные модульные тесты единицы, сборка потребителя `SysDevScen` и
allowlist-проверка корневой композиции (`IOS-AC-1`, `IOS-AC-16`).

## Traceability

| Contract ID | Layer | Method | Expected evidence | Status |
|---|---|---|---|---|
| REQ-1 | shared intake | Проверить гейт запуска: без валидной сессии доступен только флоу авторизации | Сценарий запуска на симуляторе (`simulator` check) | pending |
| REQ-2 | shared intake | Пройти email-first флоу с ветвлением и возвратом к правке почты | Сценарий `UI`-теста ветвления шагов | pending |
| REQ-3 | shared intake | Подтвердить немедленный вход в оболочку с разделом «Кейсы» после успеха | Сценарий `UI`-теста успешного входа и регистрации | pending |
| REQ-4 | shared intake | Перезапустить приложение в пределах жизни сессии | Сценарий перезапуска на симуляторе | pending |
| REQ-5 | shared intake | Пройти каждое состояние ошибок, ограничения попыток и офлайна | Набор `unit`/`UI`-проверок состояний флоу | pending |
| REQ-6 | shared intake | Смоделировать истечение или отзыв сессии на персональном запросе | Сценарий возврата на вход с проверкой хранилища | pending |
| REQ-7 | shared intake | Проверить хранилище устройства на пароль и изоляцию сессионного секрета | Инспекция хранилища после входа | pending |
| REQ-8 | shared intake | Выполнить ассистивные и appearance-проверки флоу | Свод `accessibility`-проверок на симуляторе | pending |
| REQ-9 | shared intake | Сверить шаги, тексты и гейтинг iOS с общим контрактом | Отчёт паритетного прохода флоу | pending |
| AC-1 | shared acceptance | Запуск без валидной сессии: экран входа с полем почты, навигации оболочки нет | Сценарий на симуляторе (`launch-gating`) | pending |
| AC-2 | shared acceptance | Почта существующего аккаунта ведёт к шагу с заголовком «Вход» | `UI`-тест ветвления (`email-branching-login`) | pending |
| AC-3 | shared acceptance | Почта без аккаунта ведёт к шагу с заголовком «Регистрация» | `UI`-тест ветвления (`email-branching-register`) | pending |
| AC-4 | shared acceptance | Возврат к шагу почты сохраняет введённую почту для правки | `UI`-тест возврата (`email-step-return`) | pending |
| AC-5 | shared acceptance | Верные учётные данные открывают оболочку с активными «Кейсами» | `UI`-тест входа (`login-success-entry`) | pending |
| AC-6 | shared acceptance | Валидная новая пара создаёт аккаунт и открывает оболочку | `UI`-тест регистрации (`register-success-entry`) | pending |
| AC-7 | shared acceptance | Перезапуск в пределах жизни сессии открывает оболочку без входа | Сценарий перезапуска (`session-persistence`) | pending |
| AC-8 | shared acceptance | Неверный пароль: восстановимая ошибка без раскрытия, поле очищено | Проверка состояния (`invalid-credentials`) | pending |
| AC-9 | shared acceptance | Пустое обязательное поле не отправляется, объяснение рядом с полем | Проверка валидации (`empty-field-validation`) | pending |
| AC-10 | shared acceptance | Невалидная почта отклоняется до сетевого запроса | `unit`-проверка (`local-email-validation`) | pending |
| AC-11 | shared acceptance | Короткий пароль при регистрации отклоняется до запроса | `unit`-проверка (`local-password-validation`) | pending |
| AC-12 | shared acceptance | Ограничение попыток показывает время повтора и блокирует отправку | Проверка состояния (`rate-limit-state`) | pending |
| AC-13 | shared acceptance | Занятая почта объясняет существование аккаунта и предлагает вход | Проверка состояния (`registered-email-conflict`) | pending |
| AC-14 | shared acceptance | Отсутствие сети даёт восстановимое состояние с повтором | Сценарий офлайна (`offline-recovery`) | pending |
| AC-15 | shared acceptance | Истечение сессии возвращает на вход, данные прошлой сессии скрыты | Сценарий возврата (`session-expiry-return`) | pending |
| AC-16 | shared acceptance | После возврата недействительный секрет отсутствует в хранилище | Инспекция хранилища (`stale-session-cleanup`) | pending |
| AC-17 | shared acceptance | После входа сохранённый пароль отсутствует | Инспекция хранилища (`password-not-stored`) | pending |
| AC-18 | shared acceptance | Сессионные данные недоступны другим приложениям | Инспекция хранилища (`session-storage-isolation`) | pending |
| AC-19 | shared acceptance | Ассистивные имена совпадают с подписями, состояния объявляются | `accessibility`-проверка (`assistive-semantics`) | pending |
| AC-20 | shared acceptance | Фокус переходит к началу нового шага при смене шага | `accessibility`-проверка (`focus-management`) | pending |
| AC-21 | shared acceptance | Состояния различимы без опоры только на цвет | `design-system`-проверка (`non-color-cues`) | pending |
| AC-22 | shared acceptance | Формы читаемы и работоспособны при увеличенном тексте | Проверка масштаба текста (`text-scaling`) | pending |
| AC-23 | shared acceptance | Светлое и тёмное оформление сохраняют читаемость | Скриншоты оформлений (`light-dark-appearance`) | pending |
| AC-24 | shared acceptance | Повышенно-контрастное оформление сохраняет различимость | Скриншоты контраста (`increased-contrast`) | pending |
| AC-25 | shared acceptance | Сквозной проход демонстрирует одинаковые шаги, тексты и гейтинг | Паритетный проход (`cross-client-parity`) | pending |
| IOS-REQ-1 | architecture | Проверить владение гейтом и композицией по графу проекта | Обзор границы цели приложения | pending |
| IOS-REQ-2 | presentation | Пройти ассистивный сценарий нативных controls после READY UX | Свод `accessibility`-наблюдений флоу | pending |
| IOS-REQ-3 | presentation | Проверить source и runtime на шаблон и исключённые границы | Инспекция поверхности и области действия | pending |
| IOS-REQ-4 | integration | Проверить маршрутизацию запуска по состоянию сессии | Сценарии запуска с сессией и без неё | pending |
| IOS-REQ-5 | presentation | Проверить шаги, ветвление и возврат флоу | `UI`-тесты шагов и ветвления | pending |
| IOS-REQ-6 | integration | Проверить немедленный переход в оболочку и невозвратность флоу | `UI`-тест перехода после успеха | pending |
| IOS-REQ-7 | presentation | Проверить каждое состояние валидации, ошибок, `429` и офлайна | `unit`/`UI`-матрица состояний | pending |
| IOS-REQ-8 | integration | Смоделировать `401` персонального запроса и проверить возврат | Сценарий восстановления сессии | pending |
| IOS-REQ-9 | data | Проверить обязательства хранения секрета и отсутствия пароля | Инспекция защищённого хранилища | pending |
| IOS-REQ-10 | networking | Проверить контракт клиента четырёх операций и отображение ошибок | `unit`-тесты клиента с подменой транспорта | pending |
| IOS-REQ-11 | concurrency | Проверить отмену, единственный активный запрос и блокировку повтора | `unit`-тесты конкурентности (`cancellation`, `isolation`) | pending |
| IOS-REQ-12 | architecture | Проверить физическую единицу auth и направление зависимостей | Отчёт проверки границы и графа зависимостей | pending |
| IOS-REQ-13 | parity | Сверить тексты и порядок шагов с общим контрактом | Паритетный отчёт по шагам и текстам | pending |
| IOS-AC-1 | architecture | Статический review владения гейтом и композицией | Обзор владения корневой композицией | pending |
| IOS-AC-2 | UI | Ассистивный сценарий семантики флоу на симуляторе | `accessibility`-наблюдения на симуляторе | pending |
| IOS-AC-3 | regression | Инспекция source/runtime на шаблон и исключённые границы | Регрессионная проверка поверхности | pending |
| IOS-AC-4 | UI | Запуск без сессии: загрузка, затем шаг почты, оболочка недоступна | Сценарий на симуляторе (`simulator` check) | pending |
| IOS-AC-5 | UI | Перезапуск в пределах жизни сессии открывает оболочку сразу | Сценарий перезапуска на симуляторе | pending |
| IOS-AC-6 | UI | Ветвление «Вход»/«Регистрация» и возврат с сохранением почты | `UI`-тест ветвления и возврата | pending |
| IOS-AC-7 | UI | Успешные вход и регистрация открывают оболочку с «Кейсами» | `UI`-тест успешного завершения флоу | pending |
| IOS-AC-8 | unit | Локальная валидация трёх случаев без сетевого запроса | `unit`-тесты валидации с контролем транспорта | pending |
| IOS-AC-9 | unit | Отображение `401`, `409` и `422` в наблюдаемые состояния | `unit`-тесты отображения ошибок | pending |
| IOS-AC-10 | UI | Состояние `429` с временем повтора и блокировкой отправки | Проверка состояния ограничения попыток | pending |
| IOS-AC-11 | UI | Офлайн-состояние с повтором и сохранением почты | Сценарий офлайна на симуляторе | pending |
| IOS-AC-12 | integration | Возврат по `401` персонального запроса и очистка секрета | Сценарий с инспекцией хранилища | pending |
| IOS-AC-13 | data | Инспекция хранилища: пароля нет, секрет изолирован | Отчёт инспекции защищённого хранилища | pending |
| IOS-AC-14 | unit | Контракт клиента: `https`, формат ошибок, cookie, маршрут `401` | `unit`-тесты клиента API | pending |
| IOS-AC-15 | unit | Отмена запроса, единственная отправка, консистентное состояние | `unit`-тесты конкурентности | pending |
| IOS-AC-16 | architecture | Проверка границы `Swift package` и графа зависимостей | Отчёт проверки границы (проверки `package`) | pending |
| IOS-AC-17 | UI | Сквозной паритетный проход шагов и текстов | Паритетный проход на симуляторе | pending |

## Revalidated engineering scopes and exact verify rules

Фаза `verify` перепроверит зафиксированные scopes `application`,
`concurrency`, `networking`, `package`, `ui` и применит неизменный
`applicable_rule_files` из `meta.json`. Ожидаемые проверки задач по областям
из адаптера: граница `application`; `cancellation`, `isolation`; `cache policy`,
`retry policy`; `package consumer`, `consumer integration`, `package build`,
`public contract`, `dependency graph`, `app-shell wiring`; `simulator`,
`accessibility`, `design-system`.

## Derived method matrix

- `unit` — валидация, отображение ошибок клиента, конкурентность, политика
  повторов и кэширования сетевого слоя (`IOS-AC-8`, `IOS-AC-9`, `IOS-AC-14`,
  `IOS-AC-15`).
- `UI` — сценарии флоу, гейтинга, состояний и паритета на симуляторе
  (`IOS-AC-4`–`IOS-AC-7`, `IOS-AC-10`, `IOS-AC-11`, `IOS-AC-17`).
- `integration` — перезапуск, восстановление сессии, инспекция хранилища
  (`IOS-AC-12`, `IOS-AC-13`).
- `architecture` — владение композицией, boundary guard, граф зависимостей
  (`IOS-AC-1`, `IOS-AC-16`).
- `accessibility`/`design-system` — ассистивная семантика, не-цветовые
  признаки, appearance-варианты (`IOS-AC-2`, shared `AC-19`–`AC-24`).

## Build and integration

Ожидается свежая сборка схемы `SysDevScen` с новой auth-единицей, прохождение
`SysDevScenTests`, `SysDevScenUITests` и модульных тестов package на
доступном симуляторе (`iOS 26.5`, при необходимости fallback-прогон на
`iOS 18.6`).

## Platform runtime evidence

Ожидаются свежие наблюдения runtime на симуляторе: запуск без сессии, запуск с
валидной сессией, полный проход флоу, состояния ошибок, `429` и офлайна,
возврат по истечению сессии. Каждое наблюдение фиксируется отдельным файлом в
`evidence/` этого package.

## Accessibility and design-system

Ожидаются: ассистивная проверка имён, объявлений и фокуса (`assistive-semantics`,
`focus-management`), не-цветовые признаки состояний (`non-color-cues`),
масштаб текста (`text-scaling`), соответствие ролей компонентов и
мягко-синего семантического акцента разделу `Shared Design-System Intent`
файла `specs/product/user-profile-auth/ux.md` (`design-system` check).

## Native UX verification

Будущий `platform-ux.md` (владелец — `ios-ux-designer`) обязателен для этого
product-backed `ui` package. Проверка обязана трассировать его adapter task
checks: соответствие READY `platform-ux.md`; применение `Liquid Glass` c
evidence; раздельные наблюдения `light/dark`; `increased contrast`;
`Reduce Transparency`; `Reduce Motion`; `older-OS/SDK fallback` (включая
доступный симулятор `iOS 18.6` или доказанный системный fallback). Каждое
наблюдение — отдельное конкретное evidence, без агрегации.

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

`verify` заменит `pending` на package-relative JSON observation record с
точным `obligation_id`, собственным статусом, русским наблюдением и
underlying `evidence_refs` на raw proof.

## Unverified risks

До Implement не проверены: поведение реального бэкенда `https://89.125.1.21.nip.io`
сверх зафиксированного контракта (сертификат, точные тела ошибок), достижимость
состояний `429` и офлайна в управляемых условиях симулятора, а также
совместимость `Liquid Glass`-решений будущего `platform-ux.md` со старыми
OS/SDK. Эти риски закрываются свежим evidence в фазе `verify`.
