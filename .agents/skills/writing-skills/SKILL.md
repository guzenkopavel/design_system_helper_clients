---
name: writing-skills
description: Проверять новые жёсткие workflow-правила, skills и runtime-роли через RED → GREEN → REFACTOR и сохранять test evidence. Использовать как обязательную зависимость harness-change при добавлении или существенном изменении инструктивного поведения; не использовать для typo, link fix, index и неинструктивной документации.
---

# Writing Skills

Канонический процесс: [`workflow/phases/writing-skills.md`](../../../workflow/phases/writing-skills.md).

Сначала зафиксировать падающий pressure scenario, затем внести минимальное
изменение, повторить сценарий и проверить не менее трёх сочетаний давлений.
Сохранить evidence в `workflow/test-evidence/<name>.md`.

Выбрать нативные skill и role bindings по
[`runtime-adapters`](../../../workflow/rules/runtime-adapters.md).
