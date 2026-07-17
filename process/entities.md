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
| durable product specification | `specs/product/<feature>/SPECIFICATION.md` | read-only baseline для `discovery`/`elaborate`; `archive product completed` публикует |
| shared product package | `specs/product/<feature>/` (`concept.md`, `brief.md`, UI-only `ux.md`, `spec.md`, `review-verdicts.json`) | `brainstorming`, `discovery`, `elaborate`; baseline исключён из fingerprint |
| product review subject | every active package regular file except receipt and durable `SPECIFICATION.md`; exact Status normalized | `validate-product-spec.py snapshot` |
| product review verdict | exact one-lens JSON, fresh read-only context | `product-spec-reviewer` × six |
| product review receipt | `specs/product/<feature>/review-verdicts.json` | Elaborate coordinator aggregate; downstream `check` |
| artifact language helper | `workflow/scripts/artifact_language.py` | product/platform Markdown + authored JSON validators |
| product retirement request | `specs/product/_retirement-requests/<feature>/<date-feature>.json` | `archive product` default; durable copy in product archive |
| active platform change | `<platform>/specs/<feature>/changes/<change-id>/`; intake `product-backed` или доказанный `technical-only` | `propose` → `plan` → `implement` → `verify` |
| platform UX artifact | `<platform>/specs/<feature>/changes/<change-id>/platform-ux.md` (product-backed `ui` only) | adapter UX designer → architecture/plan/implement/verify |
| platform lifecycle metadata | `<platform>/specs/<feature>/changes/<change-id>/meta.json` | `validate-platform-change.py` |
| engineering rule profile | adapter `phase_rule_profiles` + `scope_rule_profiles`; package `engineering_scopes` + exact `applicable_rule_files` | `platform_rule_profiles.py` |
| modularity adapter contract | adapter `modularity` (`isolation_scope`, platform rule, physical units) | all four lifecycle base profiles + validator/lint |
| modularity v0 compatibility anchor | `workflow/compatibility/modularity-v0.json`; exact identities + immutable meta/design/plan/task hashes | `platform_rule_profiles.py` resolver → all downstream lifecycle callers + lint |
| modularity decision | active package `design.md#Modularity decision`; `isolated | deviation | not-applicable` + structured boundary-guard verdict | architecture designer → platform boundary guard → `validate-platform-change.py` |
| platform artifact language | `workflow/rules/artifact-language.md`; Russian authored prose, exact machine/code/path exceptions | all v1 phase profiles → artifact writers → `validate-platform-change.py` + lint |
| typed task evidence | `workflow/templates/platform-task-evidence.md`; Russian summary + bounded raw technical section | implementation writer → `artifact_language.py` specialized validator |
| lifecycle capability | ordered adapter `lifecycle_capabilities`; unsupported operations fail before writes | all platform lifecycle scripts |
| planned rule selection | active package `plan/rule-selection.json`; sealed scopes, exact rules and semantic fingerprint | `plan` → downstream validators |
| plan path authority | task `Paths` = writable production через canonical no-symlink ownership helper; `Read-only context` = immutable existing refs | `plan` validator → `implement`/reconcile/pre-commit guards |
| plan task deliverables | current v1 task exact `Implementation deliverables`: минимум два substantive top-level list item о concrete artifact/behavior/boundary/test/config outcome | implementation-planner → validator → implementation-writer/reconciliation |
| implementation archive/retirement | `<platform>/specs/<feature>/archive/<date-change-id>/` + active tombstone | `archive implementation`; verified archives publish baseline, explicit retirement only unblocks active ownership |
| durable platform specification | `<platform>/specs/<feature>/SPECIFICATION.md` | read-only baseline для Propose/Plan; `archive implementation` публикует verified full contract |
| product archive | `specs/product/_archive/<feature>/<archive-id>/` + exact-path tombstone | `archive product` + retirement request |
| verification state | active package `evidence/verification-state.json` | `verify` / fingerprint capture |
| native verification obligation | exact common `NATIVE-*` row + JSON observation record under package evidence | current v1 product-backed UI Verify/recovery; v0 excluded |
| independent work lane | identity + mutable boundaries + immutable read dependencies | orchestration core; task/verify/reconcile/delivery projections |
| implementation scope baseline | schema v3 `git-visible-lane-v1` + selected index projection | `validate-implementation-scope.py` task/verify guards |
| implementation reconciliation guard | private `0600` scoped lane baseline outside repo | `reconcile-implementation` inspect/start/check before staging |
| iOS engineering rule | `iOS/workflow/rules/` | iOS addenda, adapter profiles и platform roles |
| Android engineering rule | `Android/workflow/rules/` | Android addenda, adapter profiles и platform roles |
| pre-commit gate | exact intended identity: rename mutable old/new, copy read-only source + mutable destination → private TTL receipt | portable skill + canonical change-entry helper + hook runner + `.githooks/pre-commit` |
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
