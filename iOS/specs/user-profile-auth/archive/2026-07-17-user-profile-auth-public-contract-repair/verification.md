# iOS-проверка — user-profile-auth

Фаза `verify` выполнена для пакета `user-profile-auth-public-contract-repair`.
Все итоговые строки ссылаются на доказательства внутри `evidence/`; нативные
обязательства вынесены в отдельные JSON-записи наблюдений со ссылками на
исходные доказательства.

## Modularity verification

- Dependency graph: PASS
- Public API and visibility: PASS
- Module-level tests: PASS
- Consumer integration and build: PASS
- App-shell allowlist: PASS

Доказательства: направленный граф от цели приложения к auth-единице
(`Swift package`), минимальный публичный контракт единицы, собственные
модульные тесты единицы, сборка потребителя `SysDevScen` и
allowlist-проверка корневой композиции зафиксированы в
`evidence/verification-terminal.md`.

## Traceability

| Contract ID | Layer | Method | Expected evidence | Status |
|---|---|---|---|---|
| REQ-1 | shared intake | Проверить гейт запуска: без валидной сессии доступен только флоу авторизации | evidence/verification-terminal.md | PASS |
| REQ-2 | shared intake | Пройти email-first флоу с ветвлением и возвратом к правке почты | evidence/verification-terminal.md | PASS |
| REQ-3 | shared intake | Подтвердить немедленный вход в оболочку с разделом «Кейсы» после успеха | evidence/verification-terminal.md | PASS |
| REQ-4 | shared intake | Перезапустить приложение в пределах жизни сессии | evidence/verification-terminal.md | PASS |
| REQ-5 | shared intake | Пройти каждое состояние ошибок, ограничения попыток и офлайна | evidence/verification-terminal.md | PASS |
| REQ-6 | shared intake | Смоделировать истечение или отзыв сессии на персональном запросе | evidence/verification-terminal.md | PASS |
| REQ-7 | shared intake | Проверить хранилище устройства на пароль и изоляцию сессионного секрета | evidence/verification-terminal.md | PASS |
| REQ-8 | shared intake | Выполнить ассистивные и appearance-проверки флоу | evidence/verification-terminal.md | PASS |
| REQ-9 | shared intake | Сверить шаги, тексты и гейтинг iOS с общим контрактом | evidence/verification-terminal.md | PASS |
| AC-1 | shared acceptance | Запуск без валидной сессии: экран входа с полем почты, навигации оболочки нет | evidence/verification-terminal.md | PASS |
| AC-2 | shared acceptance | Почта существующего аккаунта ведёт к шагу с заголовком «Вход» | evidence/verification-terminal.md | PASS |
| AC-3 | shared acceptance | Почта без аккаунта ведёт к шагу с заголовком «Регистрация» | evidence/verification-terminal.md | PASS |
| AC-4 | shared acceptance | Возврат к шагу почты сохраняет введённую почту для правки | evidence/verification-terminal.md | PASS |
| AC-5 | shared acceptance | Верные учётные данные открывают оболочку с активными «Кейсами» | evidence/verification-terminal.md | PASS |
| AC-6 | shared acceptance | Валидная новая пара создаёт аккаунт и открывает оболочку | evidence/verification-terminal.md | PASS |
| AC-7 | shared acceptance | Перезапуск в пределах жизни сессии открывает оболочку без входа | evidence/verification-terminal.md | PASS |
| AC-8 | shared acceptance | Неверный пароль: восстановимая ошибка без раскрытия, поле очищено | evidence/verification-terminal.md | PASS |
| AC-9 | shared acceptance | Пустое обязательное поле не отправляется, объяснение рядом с полем | evidence/verification-terminal.md | PASS |
| AC-10 | shared acceptance | Невалидная почта отклоняется до сетевого запроса | evidence/verification-terminal.md | PASS |
| AC-11 | shared acceptance | Короткий пароль при регистрации отклоняется до запроса | evidence/verification-terminal.md | PASS |
| AC-12 | shared acceptance | Ограничение попыток показывает время повтора и блокирует отправку | evidence/verification-terminal.md | PASS |
| AC-13 | shared acceptance | Занятая почта объясняет существование аккаунта и предлагает вход | evidence/verification-terminal.md | PASS |
| AC-14 | shared acceptance | Отсутствие сети даёт восстановимое состояние с повтором | evidence/verification-terminal.md | PASS |
| AC-15 | shared acceptance | Истечение сессии возвращает на вход, данные прошлой сессии скрыты | evidence/verification-terminal.md | PASS |
| AC-16 | shared acceptance | После возврата недействительный секрет отсутствует в хранилище | evidence/verification-terminal.md | PASS |
| AC-17 | shared acceptance | После входа сохранённый пароль отсутствует | evidence/verification-terminal.md | PASS |
| AC-18 | shared acceptance | Сессионные данные недоступны другим приложениям | evidence/verification-terminal.md | PASS |
| AC-19 | shared acceptance | Ассистивные имена совпадают с подписями, состояния объявляются | evidence/verification-terminal.md | PASS |
| AC-20 | shared acceptance | Фокус переходит к началу нового шага при смене шага | evidence/verification-terminal.md | PASS |
| AC-21 | shared acceptance | Состояния различимы без опоры только на цвет | evidence/verification-terminal.md | PASS |
| AC-22 | shared acceptance | Формы читаемы и работоспособны при увеличенном тексте | evidence/verification-terminal.md | PASS |
| AC-23 | shared acceptance | Светлое и тёмное оформление сохраняют читаемость | evidence/verification-terminal.md | PASS |
| AC-24 | shared acceptance | Повышенно-контрастное оформление сохраняет различимость | evidence/verification-terminal.md | PASS |
| AC-25 | shared acceptance | Сквозной проход демонстрирует одинаковые шаги, тексты и гейтинг | evidence/verification-terminal.md | PASS |
| IOS-REQ-1 | architecture | Проверить владение гейтом и композицией по графу проекта | evidence/verification-terminal.md | PASS |
| IOS-REQ-2 | presentation | Пройти ассистивный сценарий нативных controls после READY UX | evidence/verification-terminal.md | PASS |
| IOS-REQ-3 | presentation | Проверить source и runtime на шаблон и исключённые границы | evidence/verification-terminal.md | PASS |
| IOS-REQ-4 | integration | Проверить маршрутизацию запуска по состоянию сессии | evidence/verification-terminal.md | PASS |
| IOS-REQ-5 | presentation | Проверить шаги, ветвление и возврат флоу | evidence/verification-terminal.md | PASS |
| IOS-REQ-6 | integration | Проверить немедленный переход в оболочку и невозвратность флоу | evidence/verification-terminal.md | PASS |
| IOS-REQ-7 | presentation | Проверить каждое состояние валидации, ошибок, `429` и офлайна | evidence/verification-terminal.md | PASS |
| IOS-REQ-8 | integration | Смоделировать `401` персонального запроса и проверить возврат | evidence/verification-terminal.md | PASS |
| IOS-REQ-9 | data | Проверить обязательства хранения секрета и отсутствия пароля | evidence/verification-terminal.md | PASS |
| IOS-REQ-10 | networking | Проверить контракт клиента четырёх операций и отображение ошибок | evidence/verification-terminal.md | PASS |
| IOS-REQ-11 | concurrency | Проверить отмену, единственный активный запрос и блокировку повтора | evidence/verification-terminal.md | PASS |
| IOS-REQ-12 | architecture | Проверить физическую единицу auth и направление зависимостей | evidence/verification-terminal.md | PASS |
| IOS-REQ-13 | parity | Сверить тексты и порядок шагов с общим контрактом | evidence/verification-terminal.md | PASS |
| IOS-AC-1 | architecture | Статический review владения гейтом и композицией | evidence/verification-terminal.md | PASS |
| IOS-AC-2 | UI | Ассистивный сценарий семантики флоу на симуляторе | evidence/verification-terminal.md | PASS |
| IOS-AC-3 | regression | Инспекция source/runtime на шаблон и исключённые границы | evidence/verification-terminal.md | PASS |
| IOS-AC-4 | UI | Запуск без сессии: загрузка, затем шаг почты, оболочка недоступна | evidence/verification-terminal.md | PASS |
| IOS-AC-5 | UI | Перезапуск в пределах жизни сессии открывает оболочку сразу | evidence/verification-terminal.md | PASS |
| IOS-AC-6 | UI | Ветвление «Вход»/«Регистрация» и возврат с сохранением почты | evidence/verification-terminal.md | PASS |
| IOS-AC-7 | UI | Успешные вход и регистрация открывают оболочку с «Кейсами» | evidence/verification-terminal.md | PASS |
| IOS-AC-8 | unit | Локальная валидация трёх случаев без сетевого запроса | evidence/verification-terminal.md | PASS |
| IOS-AC-9 | unit | Отображение `401`, `409` и `422` в наблюдаемые состояния | evidence/verification-terminal.md | PASS |
| IOS-AC-10 | UI | Состояние `429` с временем повтора и блокировкой отправки | evidence/verification-terminal.md | PASS |
| IOS-AC-11 | UI | Офлайн-состояние с повтором и сохранением почты | evidence/verification-terminal.md | PASS |
| IOS-AC-12 | integration | Возврат по `401` персонального запроса и очистка секрета | evidence/verification-terminal.md | PASS |
| IOS-AC-13 | data | Инспекция хранилища: пароля нет, секрет изолирован | evidence/verification-terminal.md | PASS |
| IOS-AC-14 | unit | Контракт клиента: `https`, формат ошибок, cookie, маршрут `401` | evidence/verification-terminal.md | PASS |
| IOS-AC-15 | unit | Отмена запроса, единственная отправка, консистентное состояние | evidence/verification-terminal.md | PASS |
| IOS-AC-16 | architecture | Проверка границы `Swift package` и графа зависимостей | evidence/verification-terminal.md | PASS |
| IOS-AC-17 | UI | Сквозной паритетный проход шагов и текстов | evidence/verification-terminal.md | PASS |

## Revalidated engineering scopes and exact verify rules

Фаза `verify` перепроверила зафиксированные scopes `application`,
`concurrency`, `networking`, `package`, `ui` и применила неизменный
`applicable_rule_files` из `meta.json`. Проверки задач по областям из адаптера
закрыты свежим terminal evidence: граница `application`; `cancellation`,
`isolation`; `cache policy`, `retry policy`; `package consumer`,
`consumer integration`, `package build`, `public contract`, `dependency graph`,
`app-shell wiring`; `simulator`, `accessibility`, `design-system`.

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

Свежая сборка схемы `SysDevScen` с единицей авторизации прошла на симуляторе
`iPhone 17 Pro, OS=26.5`. Модульные тесты пакета `AuthFeature` прошли 45/45,
сфокусированные UI-тесты прошли 6/6 AuthFlow, 3/3 AppShell и 4/4 в матрице
запуска.

## Platform runtime evidence

Свежие runtime-наблюдения на симуляторе зафиксированы в
`evidence/verification-terminal.md`: запуск без сессии, запуск с активной
stub-сессией, полный флоу входа, полный флоу регистрации, gate оболочки и
матрица запуска для светлого/тёмного режима и ориентации. Ошибки, `429`,
offline, очистка и обязательства хранения закрыты тестами уровня пакета.

## Accessibility and design-system

Ассистивная проверка имён, объявлений и фокуса закрыта через видимые подписи и
идентификаторы `auth.*` в UI-тестах. Не-цветовые признаки, масштаб текста,
движение, прозрачность и запасной путь доступности подтверждены сочетанием
runtime UI-тестов, матрицы запуска и инспекции исходников, зафиксированным в
записях нативных наблюдений.

## Native UX verification

READY `platform-ux.md` применён как вход для этого продуктового `ui`-пакета.
Проверка трассирует adapter task checks: соответствие нативной SwiftUI
поверхности, отсутствие собственной зависимости от Liquid Glass или размытия,
раздельные наблюдения светлого и тёмного режимов, ориентации устройства,
ассистивной семантики, движения, прозрачности и запасного пути доступности.
Каждое нативное обязательство имеет отдельную JSON-запись наблюдения.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | evidence/native-appearance.json | PASS |
| NATIVE-LIGHT | evidence/native-light.json | PASS |
| NATIVE-DARK | evidence/native-dark.json | PASS |
| NATIVE-INCREASED-CONTRAST | evidence/native-increased-contrast.json | PASS |
| NATIVE-ASSISTIVE-SEMANTICS | evidence/native-assistive-semantics.json | PASS |
| NATIVE-TEXT-SCALING | evidence/native-text-scaling.json | PASS |
| NATIVE-MOTION | evidence/native-motion.json | PASS |
| NATIVE-DEVICE-ADAPTATION | evidence/native-device-adaptation.json | PASS |
| NATIVE-AVAILABILITY-FALLBACK | evidence/native-availability-fallback.json | PASS |

Каждая строка указывает JSON-запись наблюдения внутри пакета с точным
`obligation_id`, собственным статусом, русским наблюдением и ссылками
`evidence_refs` на исходные доказательства.

## Unverified risks

Живой сервер `https://89.125.1.21.nip.io` остаётся конфигурацией по умолчанию
приложения, а итоговая UI-проверка использует режим заглушки, чтобы не изменять
состояние сервера. Точные живые учётные данные и разрушающие проверки
регистрации на сервере не выполнялись; контракт клиента, HTTPS, cookie и
конверт ошибки закрыты тестами пакета.
