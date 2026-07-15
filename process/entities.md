# Harness entities

| Сущность | Каноническое размещение | Runtime binding |
|---|---|---|
| rule | `workflow/rules/` или `<platform>/workflow/rules/` | ссылка из skill/agent |
| phase | `workflow/phases/` или `<platform>/workflow/phases/` | `.agents/skills/<name>/SKILL.md` |
| skill | phase/rule, если содержит процессное знание | portable `.agents/skills/<name>/` + thin runtime entry |
| agent | `workflow/roles/<name>.md` | `.codex/agents/`, `.claude/agents/`, `.cursor/agents/`, `.opencode/agents/` |
| script | `workflow/scripts/` или `<platform>/scripts/` | вызов из phase/skill |
| template | `workflow/templates/` | ссылка из phase/skill |
| process map | `process/` | отсутствует |
| shared product package | `specs/product/<feature>/` (`concept.md`, `brief.md`, UI-only `ux.md`, `spec.md`) | `brainstorming`, `discovery`, `elaborate` |
| platform implementation package | `iOS/specs/<feature>/` либо будущий `Android/specs/<feature>/`; intake `product-backed` или доказанный `technical-only` | `propose <platform> <feature>` → `plan <platform> <feature>` |
| platform lifecycle metadata | `<platform>/specs/<feature>/meta.json` | `validate-platform-change.py` |
| iOS architecture rule | `iOS/workflow/rules/` | iOS addenda и platform roles |

Общий канон использовать, когда контракт одинаков для обеих платформ.
Платформенный канон использовать только для реальных различий SDK, build/test
tooling, архитектуры или UI automation.

Runtime matrix: [`../workflow/rules/runtime-adapters.md`](../workflow/rules/runtime-adapters.md).
Граница продуктовой и платформенной спеки:
[`specification-layers.md`](../workflow/rules/specification-layers.md).
