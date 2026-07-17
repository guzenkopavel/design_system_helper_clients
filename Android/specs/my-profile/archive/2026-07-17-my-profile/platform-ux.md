# my-profile — Android native UX

- **UX status:** `READY`
- **Platform:** `Android`
- **Source product UX:** `specs/product/my-profile/ux.md`
- **Native design language adapter:** `Material 3`
- **Color direction:** `soft blue`

## Evidence inspected

Проверены `specs/product/my-profile/ux.md`, `specs/product/my-profile/spec.md`, `Android/specs/app-shell/SPECIFICATION.md`, `Android/specs/user-profile-auth/SPECIFICATION.md`, `Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShell.kt`, `Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt` и `Android/gradle/libs.versions.toml`. Репозиторий уже использует Compose, MaterialTheme и Material 3 dependencies; доказательств M3 Expressive API как выбранного продукта или SDK-контракта нет.

```text
Material 3
MaterialTheme
color
typography
shapes
semantic tonal roles
accessible on-colors
light
dark
M3 Expressive
repository SDK/dependency/product evidence
Dynamic color
Android 12+
soft-blue fallback
```

## Shared intent mapping

Общий intent переносится без fork: профиль остаётся одной вкладкой оболочки, email является главным идентификатором, профильный символ не редактируется, «Мои интервью» доступно только после полного известного счётчика, а «Выход» завершает сессию. Android адаптирует вид через Material 3, semantic tonal roles, accessible on-colors, color и typography из MaterialTheme, не меняя общий порядок и русские тексты.

## Information architecture and navigation

Профиль остаётся destination в существующей нижней навигации. Содержимое destination заменяет placeholder на центрированную верхнюю композицию: крупный account marker, email, компактная группа действий и восстановимые сообщения состояния. Нажатие «Мои интервью» не меняет destination; успешный logout закрывает авторизованную оболочку и возвращает root auth gate к экрану ввода почты.

## Component and state mapping

Профильный символ отображается как крупный стандартный account/profile symbol с декоративной семантикой. Email отображается как текстовый элемент с assistive label текущего профиля. «Мои интервью» и «Выход» используют Material 3 action components; доступное действие получает primary или tonal role, disabled действие получает muted state и non-color cue, critical logout получает error semantic role без превращения всего экрана в warning и без потери спокойного профиля. Loading, empty, error, offline, invalid-session recovery и logout-in-progress представлены неизменяемым состоянием UI и понятными русскими сообщениями для пользователя.

## Native visual language

Нативная база строится на Material 3 и теме приложения. Композиция спокойная: тихая поверхность, запасное мягко-синее оформление для интерактивных и информационных ролей, аккуратные разделители группы действий, читаемая типографика и предсказуемые зоны касания для пользователя. M3 Expressive не включается без доказательств из репозитория; если будущая зависимость подтвердит его доступность, он остаётся условным расширением поверх тех же наблюдаемых правил и не меняет продуктовый результат.

## Color roles and appearance

Светлое, тёмное и повышенно-контрастное состояния используют доступные цвета текста для email, действий, недоступного состояния, разделителей и краткой обратной связи; это нужно для читаемости и доступности. Dynamic color не считается обязательным, потому что может увести интерфейс от soft-blue intent; если Android 12+ Dynamic color будет выбран позже, профильная единица обязана сохранить доступный soft-blue fallback и не полагаться только на персонализированную палитру, чтобы контраст оставался проверяемым.

## Accessibility and localization

Русские тексты хранятся в resources: «Мои интервью», «Выход», «Интервью: N» и восстановимые сообщения. Assistive semantics объявляет email как текущий профиль, disabled state «Мои интервью», занятость выхода и краткое сообщение с количеством. Focus order следует визуальному порядку: символ, email, состояние, действия. Touch targets, contrast, font scaling и TalkBack behavior проверяются на репрезентативном runtime с явной фиксацией результата.

## Motion and interaction

Переходы остаются спокойными и короткими: loading не мигает ложными значениями, repeated tap блокируется во время logout, snackbar или native transient feedback объявляет «Интервью: N». Motion не несёт единственный признак состояния; disabled и error состояния имеют текстовую или структурную подсказку.

## Device and layout adaptation

Экран должен сохранять читаемость на телефонах с разной высотой, при font scale, portrait и typical system insets. Content не перекрывает bottom navigation, email переносится или сокращается доступным способом без потери assistive value, группа действий остаётся компактной и не превращается во вложенную card hierarchy.

## Fallback and availability

Если история не загружена, «Мои интервью» остаётся видимым и недоступным действием с восстановимым контекстом. Если сеть недоступна, сбой logout оставляет пользователя в профиле с сообщением без ложного перехода. Если сессия недействительна, root auth recovery очищает персональные данные. Если emulator или TalkBack runtime недоступен на verify, соответствующая проверка фиксирует ограничение runtime без искусственного `PASS` и объясняет это в доказательстве на русском языке.

## Verification scenarios

Проверки покрывают светлое и тёмное оформление Material 3, повышенный контраст, доступные цвета, запасное soft-blue оформление, решение для Dynamic color, подписи TalkBack, семантику недоступности, масштаб текста, объявление краткого сообщения, занятость logout, загрузку пагинации, восстановление истории без сети и invalid-session recovery для всех важных состояний профиля. UI automation выбирается по project evidence, а отсутствие emulator фиксируется как bounded runtime limitation с русским итогом проверки и понятным статусом.

## Open gaps

None.
