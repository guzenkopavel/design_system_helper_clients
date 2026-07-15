---
name: plan
description: Декомпозировать готовую платформенную implementation spec в self-contained задачи. Использовать только по явному вызову `$plan` с платформой и фичей; сейчас поддержан iOS, Android завершается явным blocker без записи файлов.
---

# Plan

Канонический процесс: [`workflow/phases/plan.md`](../../../workflow/phases/plan.md).

1. Разобрать `$plan <platform> <feature>`. Оба аргумента обязательны; `ios`
   нормализуется в `iOS`. Feature — strict kebab-case slug без path traversal.
   Missing/unknown/`android` — blocker и **ноль записей**.
2. Потребовать `iOS/specs/<feature>/meta.json` со статусом `specified`, совпадающими
   platform/feature, закрытыми blocking questions и пройденным design gate.
3. Передать read-only context роли `repo-navigator`, boundary review роли
   `ios-package-boundary-guard`, затем единоличное владение `plan/` роли
   `implementation-planner`. Другие роли не пишут plan параллельно.
4. Создать `plan/README.md` и непрерывную последовательность `task-NNN.md`.
   Каждая задача self-contained, относится ровно к одному layer, укладывается в
   ≤2 ideal dev-days до множителей, содержит пути/зоны, inline REQ/AC context,
   зависимости, verification и expected result.
5. Для UI задач включить simulator, accessibility и design-system checks; оценки
   дать диапазонами с применимыми mobile multipliers.
6. После записи tasks выставить candidate `status: planned`, `tasks_total: N` и проверить:
   `workflow/scripts/validate-platform-change.py --platform ios --feature <feature> --mode plan`.
7. При ошибке вернуть `status: specified`, `tasks_total: 0` и сообщить blockers.

iOS-добавление: [`iOS/workflow/phases/plan.md`](../../../iOS/workflow/phases/plan.md).
Не менять spec ради удобства плана, не писать production code и не коммитить без
явной просьбы.
