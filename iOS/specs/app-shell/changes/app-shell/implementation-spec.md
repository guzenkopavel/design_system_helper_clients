# iOS implementation specification — app shell

## Intake reference

Этот iOS-пакет реализует утверждённый продуктовый ввод из
`specs/product/app-shell/spec.md`. Продуктовое поведение не описывается заново в
платформенном артефакте; решения iOS ограничены границей интеграции, нативной
семантикой и точками проверки.

## Shared contract references

Реализация и проверка трассируют `REQ-1`–`REQ-6` и `AC-1`–`AC-5` из общей
спецификации. Их наблюдаемая формулировка остаётся в общем SSOT; этот документ
не копирует и не ослабляет её.

## Platform requirements

### IOS-REQ-1 — Root composition boundary

Реализация должна заменить текущую техническую корневую поверхность через
найденные `SysDevScenApp` и путь SwiftUI-сборки. Цель приложения должна
сохранять только вход, жизненный цикл, корневую маршрутизацию, связывание
зависимостей, платформенную настройку и ресурсы target; она не должна получить
отдельную feature/data/network/persistence/reusable-UI capability.

### IOS-REQ-2 — Native control semantics

Предлагаемая замена `ContentView.swift` должна использовать стандартные
SwiftUI-средства навигации и управления, подходящие утверждённому общему
сценарию. Нативные подписи, состояние выбора, `Dynamic Type` и внешний вид
должны следовать READY-решению iOS UX и давать сфокусированную, проверяемую
accessibility-поверхность.

### IOS-REQ-3 — Template isolation

Путь замены должен убрать Core Data список, действия изменения и UI-взаимодействия
с хранением из текущей технической корневой поверхности. При этом нельзя
добавлять работу с данными, входом, аналитикой или внешними действиями вне
утверждённого ввода.

## Platform acceptance criteria

### IOS-AC-1 — Root composition result

iOS-сценарий запуска доходит до новой корневой композиции через найденную точку
входа приложения, а статический review владения подтверждает, что ответственность
остаётся только сборкой и корневой маршрутизацией.
Covers: IOS-REQ-1

### IOS-AC-2 — Native semantic interaction

Сценарий в симуляторе через выбранные стандартные controls наблюдает общий путь
договора, а assistive inspection показывает подпись каждого control и смысловое
состояние выбора без опоры только на цвет.
Covers: IOS-REQ-2

### IOS-AC-3 — Technical template removal

Сфокусированная проверка source и runtime подтверждает, что заменённая корневая
поверхность не показывает прежний Core Data список, действия добавления,
удаления и хранения, а также не добавляет исключённую границу интеграции.
Covers: IOS-REQ-3

## Constraints

`SysDevScenApp.swift`, `ContentView.swift` и Xcode project являются путями
evidence, а не разрешением предполагать package, non-application target или
конкретный SDK API. Запрещены глобальный изменяемый singleton, придуманный API
дизайн-системы и расхождение с общим поведением. Нативные визуальные решения
задаёт `platform-ux.md`; любое ограничение iOS, конфликтующее с shared behavior,
возвращает работу в product elaboration.

## Integration points

Существующий `SysDevScen` application target задаёт границу входа и композиции.
`SysDevScenTests` и `SysDevScenUITests` найдены как цели для focused unit и
UI-evidence. Xcode project остаётся источником истины для membership, scheme и
runtime discovery; никакой source path кроме документированного текущего корня
не объявляется существующим заранее.

## Open questions

Нет открытых вопросов.
