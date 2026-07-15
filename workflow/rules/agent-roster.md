# Agent roster

| Роль | Канон | Права | Runtime bindings |
|---|---|---|---|
| `implementation-writer` | [`workflow/roles/implementation-writer.md`](../roles/implementation-writer.md) | scoped write | [Codex](../../.codex/agents/implementation-writer.toml) · [Claude Code](../../.claude/agents/implementation-writer.md) · [Cursor](../../.cursor/agents/implementation-writer.md) · [OpenCode](../../.opencode/agents/implementation-writer.md) |
| `harness-auditor` | [`workflow/roles/harness-auditor.md`](../roles/harness-auditor.md) | read-only | [Codex](../../.codex/agents/harness-auditor.toml) · [Claude Code](../../.claude/agents/harness-auditor.md) · [Cursor](../../.cursor/agents/harness-auditor.md) · [OpenCode](../../.opencode/agents/harness-auditor.md) |

Платформенные роли добавлять с префиксом `ios-` или `android-`. Общую роль не
дублировать по платформам, если её контракт одинаков.
