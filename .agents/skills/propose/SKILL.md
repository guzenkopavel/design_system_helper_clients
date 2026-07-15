---
name: propose
description: Создать платформенный implementation package до написания кода. Использовать только по явному вызову `$propose` с платформой и фичей; сейчас поддержан iOS, а Android завершается явным blocker без записи файлов.
---

# Propose

Канонический процесс: [`workflow/phases/propose.md`](../../../workflow/phases/propose.md).

1. Разобрать `$propose <platform> <feature> [--tier quick|standard|extended] [--technical-only]`.
2. Потребовать оба позиционных аргумента; нормализовать `ios` в `iOS`. Неизвестная
   платформа — blocker. Feature обязан быть strict kebab-case slug без `/`, `..`
   или absolute path. `android` — `NOT IMPLEMENTED` и **ноль записей**.
3. Проверить intake по
   [`specification-layers`](../../../workflow/rules/specification-layers.md):
   `product-backed` требует `READY` + `APPROVED`, `technical-only` — доказанный
   `Product impact assessment: NONE`.
4. Собрать фактический контекст через
   `workflow/scripts/find-platform-context.py --platform ios --feature <feature> --limit 8`.
   Отделить существующие пути от greenfield-предложений.
5. Последовательно передать ownership: `repo-navigator` (read-only) →
   `specification-writer` → `architecture-designer` при required design →
   `ios-package-boundary-guard` (read-only). Конкурентных writers не запускать.
6. Создать только `iOS/specs/<feature>/`: `meta.json`, `proposal.md`,
   `implementation-spec.md`, `design.md`, `verification.md`. Не писать код и не
   копировать shared `REQ-*`/`AC-*`; ссылаться на их ID.
7. После заполнения артефактов записать candidate `status: specified` и проверить:
   `workflow/scripts/validate-platform-change.py --platform ios --feature <feature> --mode propose`.
8. При ошибке вернуть `status: draft` и сообщить blockers. Open questions,
   неполный design gate или невалидная трассировка не оставляют candidate transition.

Tier и lifecycle определяет
[`platform-change-lifecycle`](../../../workflow/rules/platform-change-lifecycle.md),
iOS adapter/addendum —
[`iOS/workflow/phases/propose.md`](../../../iOS/workflow/phases/propose.md).

Не создавать plan и production code. Не коммитить без явной просьбы.
