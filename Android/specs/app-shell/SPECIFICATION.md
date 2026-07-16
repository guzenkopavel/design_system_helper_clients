# Текущая спецификация реализации Android: app-shell

## Происхождение baseline

- **Feature:** `app-shell`
- **Платформа:** `Android`
- **Источник:** `Android/specs/app-shell/archive/2026-07-16-app-shell/implementation-spec.md`
- **SHA-256 источника:** `a28adacfe7d67a59b7b8a57b37c914e43f5a2a954c9026047d3e2ee5db6f7490`
- **Archive:** `Android/specs/app-shell/archive/2026-07-16-app-shell`
- **Receipt:** `Android/specs/app-shell/archive/2026-07-16-app-shell/archive-receipt.json`
- **Продуктовый baseline:** `specs/product/app-shell/SPECIFICATION.md`

## Текущий доставленный контракт

Реализация трассирует shared `REQ-1`–`REQ-6` и `AC-1`–`AC-5`, сохраняя общее
наблюдаемое поведение. Этот документ фиксирует полный текущий Android-контракт
границы, Material 3 semantics и интеграции.

### `AND-REQ-1` — Изолированная возможность оболочки

UI оболочки, состояние выбора, фиксированные подписи и нейтральные поверхности
предоставлены через Android library boundary с минимальным публичным
Compose-контрактом. Application entry point только компонует этот контракт и
сохраняет ответственность за lifecycle/root integration.

### `AND-REQ-2` — Нативное доступное представление навигации

Три утверждённых направления используют Material 3 semantics, видимые
non-color признаки выбора, масштабируемый текст, русские resource labels и
согласованное светлое/тёмное оформление.

## Критерии приёмки платформы

- `AND-AC-1` — Gradle graph включает library boundary без раскрытия деталей
  реализации за public Compose seam и позволяет точке входа приложения
  компоновать shell без dependency cycle. `Covers: AND-REQ-1`
- `AND-AC-2` — Сфокусированные state и Compose UI scenarios наблюдают стартовый
  выбор, выбор каждого направления, ровно один выбранный элемент, подписи и
  доступную семантику выбранности. `Covers: AND-REQ-1, AND-REQ-2`
- `AND-AC-3` — Runtime/inspection evidence покрывает светлое и тёмное оформление
  Material 3, soft-blue semantic fallback, масштабирование шрифта, TalkBack
  labels и состояние выбора без опоры только на цвет. `Covers: AND-REQ-2`

## Интеграция и ограничения

Граф Gradle включает модуль приложения и изолированную библиотечную границу;
существующие зависимости Compose/Material 3 и `MainActivity` образуют точку
композиции без логики capability в модуле приложения. Общие подписи, порядок,
стартовый выбор и границы без контента неизменны. Нельзя предполагать M3
Expressive API, Dynamic color, DI framework или хранение. Открытых вопросов по
доставленному контракту нет.
