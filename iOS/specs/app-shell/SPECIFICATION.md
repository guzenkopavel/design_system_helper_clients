# Текущая спецификация реализации iOS: app-shell

## Происхождение baseline

- **Feature:** `app-shell`
- **Платформа:** `iOS`
- **Источник:** `iOS/specs/app-shell/archive/2026-07-16-app-shell/implementation-spec.md`
- **SHA-256 источника:** `19dd6d6675e3d4a0a6d1347da7f1c13cd509617194d87556326bd6bf839cf960`
- **Archive:** `iOS/specs/app-shell/archive/2026-07-16-app-shell`
- **Receipt:** `iOS/specs/app-shell/archive/2026-07-16-app-shell/archive-receipt.json`
- **Продуктовый baseline:** `specs/product/app-shell/SPECIFICATION.md`

## Текущий доставленный контракт

Реализация трассирует shared `REQ-1`–`REQ-6` и `AC-1`–`AC-5`. Продуктовое
поведение остаётся в product baseline; этот документ фиксирует полный текущий
iOS-контракт интеграции, нативной семантики и проверки.

### `IOS-REQ-1` — Root composition boundary

`SysDevScenApp` и корневая SwiftUI-композиция предоставляют вход, lifecycle,
корневую маршрутизацию, связывание зависимостей, платформенную настройку и
ресурсы target. Оболочка приложения не владеет отдельной возможностью фичи,
данных, сети, хранения или переиспользуемого UI.

### `IOS-REQ-2` — Native control semantics

`ContentView.swift` использует стандартные SwiftUI-средства навигации и
управления для shared сценария. Русские подписи, selected state, `Dynamic Type`
и appearance дают доступную и проверяемую нативную поверхность.

### `IOS-REQ-3` — Template isolation

Корневая поверхность не содержит прежний Core Data список, действия изменения
или UI-взаимодействия с хранением и не добавляет данные, авторизацию, аналитику
или внешние действия вне product scope.

## Критерии приёмки платформы

- `IOS-AC-1` — Запуск доходит до новой root composition, а ownership review
  подтверждает только композицию и корневую маршрутизацию. `Covers: IOS-REQ-1`
- `IOS-AC-2` — Сценарий симулятора наблюдает общий путь через стандартные controls,
  а ассистивная проверка показывает подпись и состояние выбора без опоры только
  на цвет. `Covers: IOS-REQ-2`
- `IOS-AC-3` — Source/runtime evidence подтверждает отсутствие Core Data
  template interactions и исключённой интеграционной границы.
  `Covers: IOS-REQ-3`

## Интеграция и ограничения

Цель приложения `SysDevScen` остаётся границей входа и композиции;
`SysDevScenTests` и `SysDevScenUITests` дают сфокусированные свидетельства
unit/UI. Проект Xcode владеет membership, scheme и обнаружением runtime.
Запрещены глобальный изменяемый singleton, вымышленный API дизайн-системы и
расхождение с общим поведением. Открытых вопросов по доставленному контракту нет.
