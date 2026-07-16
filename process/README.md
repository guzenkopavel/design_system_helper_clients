# Process map

Карта показывает связи харнеса, но не дублирует правила. При расхождении прав
канон из `workflow/`, карту необходимо синхронизировать.

## Навигация

- [`entities.md`](entities.md) — типы сущностей и владельцы;
- [`flows.md`](flows.md) — потоки изменения харнеса, platform lifecycle и
  manual read-only deep code review;
- [`directions/_common.md`](directions/_common.md) — общий слой;
- [`directions/ios.md`](directions/ios.md) — iOS placement;
- [`directions/android.md`](directions/android.md) — Android placement.
- [`../README.md`](../README.md), [`../workflow.md`](../workflow.md) и
  [`../deep-info.md`](../deep-info.md) — объясняющие root projections разных
  уровней; канонические связи остаются в этой карте и `workflow/`.

## Edit-by-flow

1. Найти flow и scope.
2. Найти одного канонического владельца.
3. Изменить канон и только необходимые адаптеры.
4. Обновить связи в этой карте, если изменилась структура или маршрутизация.
5. Записать root documentation impact, выполнить docs render/check.
6. Запустить `$harness-review`.
