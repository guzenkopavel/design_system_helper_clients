# Mobile clients

Монорепозиторий двух нативных клиентов для симулятора и обучения работе с
дизайн-системой.

```text
iOS/       iOS-клиент
Android/   Android-клиент
specs/     общий продуктовый контракт для обоих клиентов
workflow/  канонические правила и фазы работы
process/   карта сущностей и связей харнеса
.agents/   portable skills для совместимых runtime
.codex/    роли Codex
.claude/   slash-команды и роли Claude Code; skills читаются из .agents
.cursor/   роли Cursor; skills читаются из .agents
.opencode/ slash-команды и роли OpenCode; skills читаются из .agents
```

Правила для агентов начинаются с [`AGENTS.md`](AGENTS.md).
Матрица runtime-входов описана в
[`workflow/rules/runtime-adapters.md`](workflow/rules/runtime-adapters.md).

Продуктовая проработка проходит через `brainstorming` → `discovery` →
`elaborate` и завершается общей `READY`-спекой в [`specs/product/`](specs/product/).
Для UI/interaction-фич пакет включает shared `ux.md`; `READY` требует reviews и
явного human product approval.
Платформенные implementation specs живут отдельно в [`iOS/specs/`](iOS/specs/)
и [`Android/specs/`](Android/specs/): `product-backed` требует общую
`READY`/`APPROVED`-спеку, а `technical-only` без неё допустим только при
доказанном отсутствии product impact.
