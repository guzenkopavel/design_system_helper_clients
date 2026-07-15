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
| platform implementation spec | `iOS/specs/<change>/` или `Android/specs/<change>/`; intake `product-backed` либо доказанный `technical-only` | будущий platform specification flow |

Общий канон использовать, когда контракт одинаков для обеих платформ.
Платформенный канон использовать только для реальных различий SDK, build/test
tooling, архитектуры или UI automation.

Runtime matrix: [`../workflow/rules/runtime-adapters.md`](../workflow/rules/runtime-adapters.md).
Граница продуктовой и платформенной спеки:
[`specification-layers.md`](../workflow/rules/specification-layers.md).
