# Agent roster

| Роль | Канон | Права | Runtime bindings |
|---|---|---|---|
| `implementation-writer` | [`workflow/roles/implementation-writer.md`](../roles/implementation-writer.md) | scoped write | [Codex](../../.codex/agents/implementation-writer.toml) · [Claude Code](../../.claude/agents/implementation-writer.md) · [Cursor](../../.cursor/agents/implementation-writer.md) · [OpenCode](../../.opencode/agents/implementation-writer.md) |
| `harness-auditor` | [`workflow/roles/harness-auditor.md`](../roles/harness-auditor.md) | read-only | [Codex](../../.codex/agents/harness-auditor.toml) · [Claude Code](../../.claude/agents/harness-auditor.md) · [Cursor](../../.cursor/agents/harness-auditor.md) · [OpenCode](../../.opencode/agents/harness-auditor.md) |
| `repo-navigator` | [`workflow/roles/repo-navigator.md`](../roles/repo-navigator.md) | read-only | [Codex](../../.codex/agents/repo-navigator.toml) · [Claude Code](../../.claude/agents/repo-navigator.md) · [Cursor](../../.cursor/agents/repo-navigator.md) · [OpenCode](../../.opencode/agents/repo-navigator.md) |
| `specification-writer` | [`workflow/roles/specification-writer.md`](../roles/specification-writer.md) | proposal/spec/verification | [Codex](../../.codex/agents/specification-writer.toml) · [Claude Code](../../.claude/agents/specification-writer.md) · [Cursor](../../.cursor/agents/specification-writer.md) · [OpenCode](../../.opencode/agents/specification-writer.md) |
| `architecture-designer` | [`workflow/roles/architecture-designer.md`](../roles/architecture-designer.md) | design only | [Codex](../../.codex/agents/architecture-designer.toml) · [Claude Code](../../.claude/agents/architecture-designer.md) · [Cursor](../../.cursor/agents/architecture-designer.md) · [OpenCode](../../.opencode/agents/architecture-designer.md) |
| `implementation-planner` | [`workflow/roles/implementation-planner.md`](../roles/implementation-planner.md) | plan only | [Codex](../../.codex/agents/implementation-planner.toml) · [Claude Code](../../.claude/agents/implementation-planner.md) · [Cursor](../../.cursor/agents/implementation-planner.md) · [OpenCode](../../.opencode/agents/implementation-planner.md) |
| `ios-package-boundary-guard` | [`iOS/workflow/roles/ios-package-boundary-guard.md`](../../iOS/workflow/roles/ios-package-boundary-guard.md) | read-only iOS | [Codex](../../.codex/agents/ios-package-boundary-guard.toml) · [Claude Code](../../.claude/agents/ios-package-boundary-guard.md) · [Cursor](../../.cursor/agents/ios-package-boundary-guard.md) · [OpenCode](../../.opencode/agents/ios-package-boundary-guard.md) |

Платформенные роли добавлять с префиксом `ios-` или `android-`. Общую роль не
дублировать по платформам, если её контракт одинаков.

Artifact owners работают последовательно: `specification-writer` →
`architecture-designer` → `implementation-planner`. Одновременная запись одного
package запрещена.
