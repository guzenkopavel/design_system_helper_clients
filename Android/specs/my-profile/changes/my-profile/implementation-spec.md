# Implementation spec — my-profile / Android / my-profile

## Intake reference

Реализация следует утверждённому shared product contract в `specs/product/my-profile/spec.md`. Android адаптирует наблюдаемое поведение через существующую auth gate, shell destination, Material 3 Compose UI, repository/data boundary и coroutine-based pagination без копирования или ослабления shared требований.

## Shared contract references

Shared `REQ-1`–`REQ-10` и `AC-1`–`AC-18` остаются владением продуктового слоя. Android package ссылается на них через платформенные `AND-REQ` и `AND-AC`, а полный наблюдаемый текст остаётся в `specs/product/my-profile/spec.md`.

| Shared ID | Android trace |
|---|---|
| `REQ-1` | `AND-REQ-1`, `AND-REQ-2`, `AND-REQ-8` |
| `REQ-2` | `AND-REQ-3`, `AND-REQ-4` |
| `REQ-3` | `AND-REQ-5` |
| `REQ-4` | `AND-REQ-6` |
| `REQ-5` | `AND-REQ-5` |
| `REQ-6` | `AND-REQ-7`, `AND-REQ-10` |
| `REQ-7` | `AND-REQ-9`, `AND-REQ-10` |
| `REQ-8` | `AND-REQ-11` |
| `REQ-9` | `AND-REQ-8`, `AND-REQ-12` |
| `REQ-10` | `AND-REQ-12` |

## Platform requirements

### AND-REQ-1 — Изолированная Android capability профиля

Профиль реализуется в отдельной библиотечной единице Gradle Android с минимальным публичным Compose-контрактом. Эта единица владеет состоянием UI профиля, repository профиля, политикой счётчика истории, действием logout и ресурсами профиля. Application module только создаёт зависимости, передаёт callbacks и компонует возможность в корневой граф.

### AND-REQ-2 — Интеграция с существующей оболочкой

Profile destination в существующей оболочке получает реальное content slot или эквивалентную публичную seam без переноса profile logic в `:app-shell`. Навигационная chrome, выбранность вкладки и labels оболочки остаются совместимыми с baseline `app-shell`.

### AND-REQ-3 — Загрузка текущего профиля

Android repository запрашивает текущий профиль по серверной сессии, отдаёт в presentation state только email и не раскрывает технический `id` в UI. До успешной загрузки персональные значения не отображаются как готовые.

### AND-REQ-4 — Полный счётчик истории интервью

History repository загружает страницы истории текущей серверной сессии до завершения pagination. Presentation state считает действие «Мои интервью» готовым только после полного известного количества; first page не считается полным доказательством при наличии следующей страницы.

### AND-REQ-5 — Условная доступность «Мои интервью»

Compose UI всегда показывает действие «Мои интервью», но включает обработку нажатия только при полном известном количестве больше нуля. При нуле, загрузке, ошибке или offline-состоянии без известного счётчика действие остаётся видимым и недоступным, с признаком не только цветом и ассистивной семантикой недоступности.

### AND-REQ-6 — Краткое сообщение с количеством

Нажатие доступного действия «Мои интервью» показывает native transient feedback с текстом «Интервью: N», где `N` берётся из полного state counter. Feedback не меняет выбранную вкладку, не открывает новый screen и объявляется ассистивно.

### AND-REQ-7 — Logout и возврат к auth gate

Действие «Выход» вызывает logout через repository, блокирует повторную отправку на время запроса и при успехе сообщает root composition о завершении сессии. Root auth gate открывает первый экран ввода почты с пустым значением и без персональных данных профиля.

### AND-REQ-8 — Material 3 профильный экран

Интерфейс использует Material 3 и MaterialTheme, а цвет, типографика, формы, семантические tonal roles и доступные on-colors берутся из темы. Профильный символ крупный и стандартный, email находится под ним, действия собраны компактно, а тихая поверхность и запасное soft-blue оформление сохраняют общий визуальный замысел и читаемую иерархию.

### AND-REQ-9 — Ошибки истории и offline recovery

Ошибка загрузки истории или отсутствие сети отображается как восстановимое состояние профиля. «Мои интервью» не активируется до успешного определения счётчика; «Выход» остаётся доступным, если сессия всё ещё считается авторизованной.

### AND-REQ-10 — Invalid session recovery и privacy cleanup

Недействительная сессия при запросе профиля или истории возвращает корневое auth recovery по baseline `user-profile-auth`. Email, счётчик и любые данные истории прошлого профиля не остаются видимыми после потери авторизации.

### AND-REQ-11 — Cross-client parity на Android

Android сохраняет тот же набор состояний, русских текстов, правил доступности actions, результата logout и no-navigation behavior для «Мои интервью», который задан shared package для обеих платформ.

### AND-REQ-12 — Accessibility, localization и adaptive appearance

Все пользовательские строки хранятся в resources. Семантика объявляет email, подписи действий, недоступное состояние, занятость logout и краткую обратную связь. Экран поддерживает увеличение текста, light, dark, increased contrast и признаки состояний не только цветом.

## Platform acceptance criteria

### AND-AC-1 — Gradle module boundary

Граф Gradle включает отдельную библиотечную единицу профиля, а `:app` зависит от её публичного контракта без владения логикой профиля.

Covers: AND-REQ-1

### AND-AC-2 — Shell content seam

Profile destination в оболочке показывает profile content через публичную seam, сохраняя выбранность нижней навигации, labels и app-shell baseline behavior.

Covers: AND-REQ-2

### AND-AC-3 — Profile content

Авторизованный пользователь на вкладке профиля видит крупный standard account marker, email текущего профиля и actions «Мои интервью» / «Выход».

Covers: AND-REQ-3, AND-REQ-8

### AND-AC-4 — Pagination completion

Проверки repository подтверждают, что страницы истории загружаются до терминального состояния пагинации перед публикацией полного счётчика.

Covers: AND-REQ-4

### AND-AC-5 — Enabled action when count positive

При полном известном `count > 0` action «Мои интервью» активен и имеет click handling.

Covers: AND-REQ-5

### AND-AC-6 — Disabled action when count zero or unknown

При `count = 0`, загрузке, ошибке истории или offline-состоянии без известного счётчика действие «Мои интервью» видимо, недоступно, не вызывает обработку нажатия и различимо не только цветом.

Covers: AND-REQ-5, AND-REQ-9

### AND-AC-7 — Count feedback

Нажатие активного action показывает transient feedback «Интервью: N» и оставляет пользователя на profile destination.

Covers: AND-REQ-6

### AND-AC-8 — Successful logout routing

Успешный logout переводит root composition в auth flow на экран ввода почты с пустым полем.

Covers: AND-REQ-7

### AND-AC-9 — Logout failure recovery

Сетевой сбой logout оставляет пользователя в профиле, показывает восстановимое сообщение и не очищает UI так, будто выход уже завершён.

Covers: AND-REQ-7, AND-REQ-9

### AND-AC-10 — Invalid session cleanup

Недействительная сессия при profile или history request возвращает в auth recovery и убирает email и history-derived state прошлого профиля с экрана.

Covers: AND-REQ-10

### AND-AC-11 — Material 3 appearance

UI профиля использует роли темы Material 3, soft-blue fallback, accessible on-colors, light, dark и increased contrast states без зависимости только от Dynamic color.

Covers: AND-REQ-8, AND-REQ-12

### AND-AC-12 — Assistive semantics

Assistive проверка объявляет email текущего профиля, labels «Мои интервью» и «Выход», disabled state, feedback «Интервью: N» и busy state logout.

Covers: AND-REQ-12

### AND-AC-13 — Font scaling and layout

При увеличенном тексте профильный символ, email, сообщение состояния и действия остаются читаемыми, не перекрывают нижнюю навигацию и не ломают touch targets.

Covers: AND-REQ-12

### AND-AC-14 — Localization resources

Пользовательские строки «Мои интервью», «Выход», «Интервью: N» и recovery messages принадлежат resources profile module и проверяются с format arguments.

Covers: AND-REQ-12

### AND-AC-15 — Cross-client observable parity

Фокусные Android-сценарии подтверждают тот же наблюдаемый набор состояний, обратную связь без навигации и результат logout, что и shared contract.

Covers: AND-REQ-11

## Constraints

Пакет не владеет backend, OpenAPI, новым экраном истории, деталями интервью, пользовательским аватаром, редактированием профиля, analytics, политикой Dynamic color или внедрением M3 Expressive. `:app` остаётся поверхностью корневой композиции и настройки зависимостей; `:app-shell` остаётся навигационной рамкой и не владеет данными профиля, network, repository или изменяемым состоянием профиля.

## Integration points

`Android/settings.gradle.kts` получает include новой единицы. `Android/app/build.gradle.kts` зависит от публичного контракта профиля. `Android/app-shell` получает content seam для destination, если текущего контракта недостаточно. `Android/auth` продолжает владеть session/auth baseline; профильная единица использует переданную session-aware network boundary и сообщает о недействительной сессии или результате logout через callbacks. API base URL остаётся внешней конфигурацией.

## Open questions

None.
