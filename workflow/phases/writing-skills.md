---
phase: writing-skills
writes_artifacts:
  - workflow/test-evidence/<name>.md
requires_verification: true
recommended_roles:
  - implementation-writer
  - harness-auditor
---

# Phase: Writing Skills

Не добавлять жёсткое правило, новый skill или новую роль без наблюдаемого
падающего сценария до изменения.

1. RED: выполнить реалистичный pressure scenario без нового правила и сохранить
   конкретный failure.
2. GREEN: внести минимальное изменение и повторить тот же сценарий.
3. REFACTOR: проверить не менее трёх сочетаний давлений и убрать лишний текст.
4. Сохранить задачу, baseline, результат и остаточные ограничения в
   `workflow/test-evidence/<name>.md`.

Пропускать фазу для typo, форматирования, link fix, index/catalog и документации
без инструктивного поведения.
