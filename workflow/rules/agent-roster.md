# Agent roster

| Роль | Канон | Права | Runtime bindings |
|---|---|---|---|
| `implementation-writer` | [`workflow/roles/implementation-writer.md`](../roles/implementation-writer.md) | scoped write | [Codex](../../.codex/agents/implementation-writer.toml) · [Claude Code](../../.claude/agents/implementation-writer.md) · [Cursor](../../.cursor/agents/implementation-writer.md) · [OpenCode](../../.opencode/agents/implementation-writer.md) |
| `product-spec-reviewer` | [`workflow/roles/product-spec-reviewer.md`](../roles/product-spec-reviewer.md) | read-only, one package/lens/fingerprint | [Codex](../../.codex/agents/product-spec-reviewer.toml) · [Claude Code](../../.claude/agents/product-spec-reviewer.md) · [Cursor](../../.cursor/agents/product-spec-reviewer.md) · [OpenCode](../../.opencode/agents/product-spec-reviewer.md) |
| `implementation-discovery` | [`workflow/roles/implementation-discovery.md`](../roles/implementation-discovery.md) | read-only | [Codex](../../.codex/agents/implementation-discovery.toml) · [Claude Code](../../.claude/agents/implementation-discovery.md) · [Cursor](../../.cursor/agents/implementation-discovery.md) · [OpenCode](../../.opencode/agents/implementation-discovery.md) |
| `verifier` | [`workflow/roles/verifier.md`](../roles/verifier.md) | read-only production; scoped evidence | [Codex](../../.codex/agents/verifier.toml) · [Claude Code](../../.claude/agents/verifier.md) · [Cursor](../../.cursor/agents/verifier.md) · [OpenCode](../../.opencode/agents/verifier.md) |
| `harness-auditor` | [`workflow/roles/harness-auditor.md`](../roles/harness-auditor.md) | read-only | [Codex](../../.codex/agents/harness-auditor.toml) · [Claude Code](../../.claude/agents/harness-auditor.md) · [Cursor](../../.cursor/agents/harness-auditor.md) · [OpenCode](../../.opencode/agents/harness-auditor.md) |
| `deep-code-reviewer` | [`workflow/roles/deep-code-reviewer.md`](../roles/deep-code-reviewer.md) | read-only | [Codex](../../.codex/agents/deep-code-reviewer.toml) · [Claude Code](../../.claude/agents/deep-code-reviewer.md) · [Cursor](../../.cursor/agents/deep-code-reviewer.md) · [OpenCode](../../.opencode/agents/deep-code-reviewer.md) |
| `bug-investigator` | [`workflow/roles/bug-investigator.md`](../roles/bug-investigator.md) | read-only | [Codex](../../.codex/agents/bug-investigator.toml) · [Claude Code](../../.claude/agents/bug-investigator.md) · [Cursor](../../.cursor/agents/bug-investigator.md) · [OpenCode](../../.opencode/agents/bug-investigator.md) |
| `security-reviewer` | [`workflow/roles/security-reviewer.md`](../roles/security-reviewer.md) | read-only | [Codex](../../.codex/agents/security-reviewer.toml) · [Claude Code](../../.claude/agents/security-reviewer.md) · [Cursor](../../.cursor/agents/security-reviewer.md) · [OpenCode](../../.opencode/agents/security-reviewer.md) |
| `repo-navigator` | [`workflow/roles/repo-navigator.md`](../roles/repo-navigator.md) | read-only | [Codex](../../.codex/agents/repo-navigator.toml) · [Claude Code](../../.claude/agents/repo-navigator.md) · [Cursor](../../.cursor/agents/repo-navigator.md) · [OpenCode](../../.opencode/agents/repo-navigator.md) |
| `specification-writer` | [`workflow/roles/specification-writer.md`](../roles/specification-writer.md) | proposal/spec/verification | [Codex](../../.codex/agents/specification-writer.toml) · [Claude Code](../../.claude/agents/specification-writer.md) · [Cursor](../../.cursor/agents/specification-writer.md) · [OpenCode](../../.opencode/agents/specification-writer.md) |
| `ios-ux-designer` | [`iOS/workflow/roles/ios-ux-designer.md`](../../iOS/workflow/roles/ios-ux-designer.md) | iOS platform-ux.md only | [Codex](../../.codex/agents/ios-ux-designer.toml) · [Claude Code](../../.claude/agents/ios-ux-designer.md) · [Cursor](../../.cursor/agents/ios-ux-designer.md) · [OpenCode](../../.opencode/agents/ios-ux-designer.md) |
| `android-ux-designer` | [`Android/workflow/roles/android-ux-designer.md`](../../Android/workflow/roles/android-ux-designer.md) | Android platform-ux.md only | [Codex](../../.codex/agents/android-ux-designer.toml) · [Claude Code](../../.claude/agents/android-ux-designer.md) · [Cursor](../../.cursor/agents/android-ux-designer.md) · [OpenCode](../../.opencode/agents/android-ux-designer.md) |
| `architecture-designer` | [`workflow/roles/architecture-designer.md`](../roles/architecture-designer.md) | design only | [Codex](../../.codex/agents/architecture-designer.toml) · [Claude Code](../../.claude/agents/architecture-designer.md) · [Cursor](../../.cursor/agents/architecture-designer.md) · [OpenCode](../../.opencode/agents/architecture-designer.md) |
| `implementation-planner` | [`workflow/roles/implementation-planner.md`](../roles/implementation-planner.md) | plan only | [Codex](../../.codex/agents/implementation-planner.toml) · [Claude Code](../../.claude/agents/implementation-planner.md) · [Cursor](../../.cursor/agents/implementation-planner.md) · [OpenCode](../../.opencode/agents/implementation-planner.md) |
| `ios-package-boundary-guard` | [`iOS/workflow/roles/ios-package-boundary-guard.md`](../../iOS/workflow/roles/ios-package-boundary-guard.md) | read-only iOS | [Codex](../../.codex/agents/ios-package-boundary-guard.toml) · [Claude Code](../../.claude/agents/ios-package-boundary-guard.md) · [Cursor](../../.cursor/agents/ios-package-boundary-guard.md) · [OpenCode](../../.opencode/agents/ios-package-boundary-guard.md) |
| `android-package-boundary-guard` | [`Android/workflow/roles/android-package-boundary-guard.md`](../../Android/workflow/roles/android-package-boundary-guard.md) | read-only Android placement | Codex · Claude Code · Cursor · OpenCode bindings |
| `android-kotlin-reviewer` | [`Android/workflow/roles/android-kotlin-reviewer.md`](../../Android/workflow/roles/android-kotlin-reviewer.md) | read-only Android review | Codex · Claude Code · Cursor · OpenCode bindings |
| `android-build-diagnostician` | [`Android/workflow/roles/android-build-diagnostician.md`](../../Android/workflow/roles/android-build-diagnostician.md) | read-only diagnostics | Codex · Claude Code · Cursor · OpenCode bindings |

Платформенные роли добавлять с префиксом `ios-` или `android-`. Общую роль не
дублировать по платформам, если её контракт одинаков.

Artifact owners работают последовательно: `specification-writer` → conditional
adapter UX designer для product-backed `ui` → `architecture-designer` →
`implementation-planner` → `implementation-writer`
(`platform-implementation`) → `verifier`. Discovery/review роли не пишут
production; одновременная запись одного package запрещена.

Product elaboration запускает `product-spec-reviewer` ровно шесть раз в
отдельных fresh contexts: один package/lens/fingerprint на invocation. Роль не
становится artifact owner и не читает outputs других lenses.
