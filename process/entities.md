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
| repository documentation rule | `workflow/rules/repository-documentation.md` | `harness-change` + `harness-review` + `harness-docs.py` |
| root documentation projection | `README.md`, `workflow.md`, `deep-info.md` | exact generated blocks + manual semantic audit |
| shared product package | `specs/product/<feature>/` (`concept.md`, `brief.md`, UI-only `ux.md`, `spec.md`, `review-verdicts.json`) | `brainstorming`, `discovery`, `elaborate` |
| product review subject | every active package regular file except receipt; exact Status normalized | `validate-product-spec.py snapshot` |
| product review verdict | exact one-lens JSON, fresh read-only context | `product-spec-reviewer` × six |
| product review receipt | `specs/product/<feature>/review-verdicts.json` | Elaborate coordinator aggregate; downstream `check` |
| active platform change | `<platform>/specs/<feature>/changes/<change-id>/`; intake `product-backed` или доказанный `technical-only` | `propose` → `plan` → `implement` → `verify` |
| platform UX artifact | `<platform>/specs/<feature>/changes/<change-id>/platform-ux.md` (product-backed `ui` only) | adapter UX designer → architecture/plan/implement/verify |
| platform lifecycle metadata | `<platform>/specs/<feature>/changes/<change-id>/meta.json` | `validate-platform-change.py` |
| engineering rule profile | adapter `phase_rule_profiles` + `scope_rule_profiles`; package `engineering_scopes` + exact `applicable_rule_files` | `platform_rule_profiles.py` |
| modularity adapter contract | adapter `modularity` (`isolation_scope`, platform rule, physical units) | all four lifecycle base profiles + validator/lint |
| modularity v0 compatibility anchor | `workflow/compatibility/modularity-v0.json`; exact identities + immutable meta/design/plan/task hashes | `platform_rule_profiles.py` resolver → all downstream lifecycle callers + lint |
| modularity decision | active package `design.md#Modularity decision`; `isolated | deviation | not-applicable` + structured boundary-guard verdict | architecture designer → platform boundary guard → `validate-platform-change.py` |
| platform artifact language | `workflow/rules/artifact-language.md`; Russian authored prose, exact machine/code/path exceptions | all v1 phase profiles → artifact writers → `validate-platform-change.py` + lint |
| lifecycle capability | ordered adapter `lifecycle_capabilities`; unsupported operations fail before writes | all platform lifecycle scripts |
| planned rule selection | active package `plan/rule-selection.json`; sealed scopes, exact rules and semantic fingerprint | `plan` → downstream validators |
| implementation archive | `<platform>/specs/<feature>/archive/<date-change-id>/` + active tombstone | `archive implementation` |
| product archive | `specs/product/_archive/<feature>/<archive-id>/` + exact-path tombstone | `archive product` + retirement request |
| verification state | active package `evidence/verification-state.json` | `verify` / fingerprint capture |
| implementation reconciliation guard | private `0600` baseline outside repo + selected active package | `reconcile-implementation` inspect/start/check before staging |
| iOS engineering rule | `iOS/workflow/rules/` | iOS addenda, adapter profiles и platform roles |
| Android engineering rule | `Android/workflow/rules/` | Android addenda, adapter profiles и platform roles |
| pre-commit gate | `workflow/phases/pre-commit-check.md` + `workflow/scripts/pre-commit-check.py` | portable skill + `.githooks/pre-commit` |
| runtime hook policy | `workflow/rules/hook-contract.md` + `workflow/hooks/hook-runner.py` | thin Codex/Claude/Cursor/OpenCode bindings |
| platform pre-commit profile | `<platform>/workflow/platform-contract.json#pre_commit` | platform addendum + common staged gate |
| deep review invocation | `workflow/phases/deep-code-review.md` + common review rules | manual-only portable `deep-code-review`; read-only runtime roles |
| harness security scan | `workflow/scripts/harness-security-audit.py` | `deep-code-review security` + non-recursive `harness-lint` check |
| deep review mutation guard | private `0600` ephemeral state outside repo; no repository artifact | mandatory `start`/`check` around every deep-code-review mode |

Общий канон использовать, когда контракт одинаков для обеих платформ.
Платформенный канон использовать только для реальных различий SDK, build/test
tooling, архитектуры или UI automation.

Runtime matrix: [`../workflow/rules/runtime-adapters.md`](../workflow/rules/runtime-adapters.md).
Граница продуктовой и платформенной спеки:
[`specification-layers.md`](../workflow/rules/specification-layers.md).
