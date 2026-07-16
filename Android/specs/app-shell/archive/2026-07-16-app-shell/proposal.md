# Proposal — app shell / Android / app-shell

## Intake

Это product-backed изменение для Android. `specs/product/app-shell/spec.md`
имеет статус `READY` и явное `APPROVED`; проверенный общий контракт остаётся
единственным источником наблюдаемого поведения, подписей, порядка, стартового
выбора и parity между платформами.

## Goal

Заменить сгенерированное приветствие на нативную Android-оболочку приложения:
она показывает три утверждённых направления и их нейтральные поверхности,
остаётся доступной и не добавляет продуктового поведения вне общего контракта.

## Scope

Изменение вводит proposed Android library boundary для app-shell capability,
Compose-навигацию и состояние, root composition в существующей точке входа,
Gradle-включение, русские строковые ресурсы и focused UI/state verification.
Документ ссылается на shared `REQ` и `AC`, но не копирует их текст и не
ослабляет общий контракт.

## Engineering scope selection

`application` покрывает существующую границу composition в `MainActivity`;
`compose` и `ui` подтверждены текущей настройкой Compose Material 3; `gradle`
и `module` нужны для добавления physical boundary в обнаруженный one-module
build; `localization` владеет фиксированными русскими подписями в module
resources. Для `data`, `network`, `persistence`, `concurrency` и
`multiplatform` нет ни repository evidence, ни product evidence.

## Applicable rule files

Точный набор правил lifecycle для Propose зафиксирован в `meta.json`: общие
правила спецификации, системного дизайна и модульности; Android-архитектура и
модульность; а также профили шести выбранных областей инженерной работы. Plan
сохраняет этот выбор через снимок resolver, а последующие фазы не добавляют
новые области.

## Non-goals

Изменение не добавляет реальное содержимое разделов, поведение аккаунта,
хранение, сеть, аналитику, deep links, разрешения, Dynamic color,
M3 Expressive-оформление или реализацию будущих разделов. Реализация для iOS
остаётся вне этого Android package.

## Accepted decisions

Независимым владельцем навигационной возможности выбран proposed Gradle
Android library module; существующая точка входа приложения сохраняет только
ответственность за композицию. Material 3 является нативной базой, а
`platform-ux.md` переводит общий спокойный soft-blue intent в семантические
роли и доступные fallback-решения.

## Open questions

None.

## Risks

Текущий граф содержит только `:app`, поэтому первая implementation-задача
сначала должна подключить и собрать proposed library boundary, а уже потом
проверять поведение UI. Доступность Android runtime, масштабирование шрифта,
семантика TalkBack, тёмное оформление и high-contrast presentation требуют
focused evidence, а не предположений.
