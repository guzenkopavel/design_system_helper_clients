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
   `elaborate`, `propose`, `plan`, `implement`, `verify`, `archive`,
   `deep-code-review`, `harness-change`, `harness-review` и `writing-skills`;
2. загружать полный portable `SKILL.md` до действий;
3. резолвить все роли из [`agent-roster.md`](agent-roster.md), включая
   зарегистрированные platform guards;
4. соблюдать permissions: auditor read-only, writer scoped write;
5. передавать аргументы пользователя без изменения смысла;
6. читать общий [`AGENTS.md`](../../AGENTS.md) напрямую или через runtime entry.

Claude Code не должен создавать одноимённые `.claude/skills/<name>/SKILL.md`:
OpenCode также сканирует этот namespace и может недетерминированно выбрать
runtime-копию вместо portable SSOT. Явный Claude UX сохраняется через thin
`.claude/commands/<name>.md`.

`propose`, `plan`, `implement`, `verify`, `archive` и `deep-code-review` — manual-only во всех
runtime. Их adapters передают identity/flags без перестановки. Platform
implementation lifecycle всегда требует `<platform> <feature>`; Android пока
поддерживает propose/plan/implement, а verify/implementation archive возвращают
unsupported до любых записей по machine capability. Product archive не принимает platform,
но требует validated retirement request.

`deep-code-review review|feedback|bug` требует platform identity и одинаковый
read-only role contract во всех runtime; `security` не принимает platform.
Runtime не добавляет fix mode и не превращает same-context fallback в
independent review.

Если конкретная версия runtime обнаруживает skill, но не предоставляет механизм
custom subagent, выполнить writer и review последовательно в основной сессии.
Перед review прекратить любые записи, явно отметить fallback в отчёте и не
заявлять независимое ревью.

## Hook adapters

Hook policy принадлежит [`hook-contract.md`](hook-contract.md) и исполняется
только [`../hooks/hook-runner.py`](../hooks/hook-runner.py). Thin bindings:

| Runtime | Binding | Enforcement |
|---|---|---|
| Codex | `.codex/hooks.json` | deny зависит от поддержки exit `2`; post output остаётся generic/advisory |
| Claude Code | `.claude/settings.json` | blocking `PreToolUse`; native `PostToolUse.additionalContext` warning |
| Cursor | `.cursor/hooks.json` | `preToolUse` permission/fail-closed deny; `postToolUse.additional_context` warning |
| OpenCode | `.opencode/plugins/harness-hooks.ts` | auto-loaded worktree-root plugin превращает deny/failure в error и показывает warning |

Адаптеры передают JSON stdin и не содержат собственных Git, secret, platform
или task-coverage правил. Независимо от runtime, финальная обязательная граница —
tracked [`.githooks/pre-commit`](../../.githooks/pre-commit), запускающий staged
gate. Наличие tracked hook не означает его автоматическую установку.
