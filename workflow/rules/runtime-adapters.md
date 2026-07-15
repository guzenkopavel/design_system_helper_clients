# Runtime adapters

Portable skill SSOT находится в `.agents/skills/<name>/SKILL.md`. Не копировать
его тело в runtime-каталоги.

| Runtime | Skill discovery | Явный вызов | Role binding |
|---|---|---|---|
| Codex | `.agents/skills/` | `$<skill>` или выбор через `/skills` | `.codex/agents/*.toml` |
| Claude Code | `.claude/commands/<skill>.md` → `.agents/skills/` | `/<skill>` | `.claude/agents/*.md` |
| Cursor | `.agents/skills/` | `/<skill>` | `.cursor/agents/*.md` |
| OpenCode | `.agents/skills/` через native skill tool | `/<skill>` из `.opencode/commands/` | `.opencode/agents/*.md` |

## Adapter contract

Каждый runtime должен:

1. обнаруживать все portable skills, включая `brainstorming`, `discovery`,
   `elaborate`, `harness-change`, `harness-review` и `writing-skills`;
2. загружать полный portable `SKILL.md` до действий;
3. резолвить роли `implementation-writer` и `harness-auditor`;
4. соблюдать permissions: auditor read-only, writer scoped write;
5. передавать аргументы пользователя без изменения смысла;
6. читать общий [`AGENTS.md`](../../AGENTS.md) напрямую или через runtime entry.

Claude Code не должен создавать одноимённые `.claude/skills/<name>/SKILL.md`:
OpenCode также сканирует этот namespace и может недетерминированно выбрать
runtime-копию вместо portable SSOT. Явный Claude UX сохраняется через thin
`.claude/commands/<name>.md`.

Если конкретная версия runtime обнаруживает skill, но не предоставляет механизм
custom subagent, выполнить writer и review последовательно в основной сессии.
Перед review прекратить любые записи, явно отметить fallback в отчёте и не
заявлять независимое ревью.
