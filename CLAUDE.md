@AGENTS.md

# Claude Code adapter

Процессный канон находится в [`workflow/`](workflow/). Явные slash-входы
находятся в `.claude/commands/` и загружают portable SSOT из `.agents/skills/`.
Одноимённые копии в `.claude/skills/` не создавать. Нативные роли находятся в
`.claude/agents/` и делегируют контракты из `workflow/roles/`.
