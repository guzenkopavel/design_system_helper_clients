# Workflow

Канонический, независимый от runtime слой процесса.

## Фазы

- [`phases/brainstorming.md`](phases/brainstorming.md) — исследовать сырую
  продуктовую идею и реальные альтернативы;
- [`phases/discovery.md`](phases/discovery.md) — собрать общий product brief для
  iOS и Android;
- [`phases/elaborate.md`](phases/elaborate.md) — довести общий продуктовый пакет
  до `READY` и остановиться до platform fan-out;
- [`phases/propose.md`](phases/propose.md) — создать implementation package
  выбранной платформы через её runtime adapter;
- [`phases/plan.md`](phases/plan.md) — декомпозировать `specified` package в
  self-contained задачи;
- [`phases/implement.md`](phases/implement.md) — выполнить ready task в
  adapter-owned production scope;
- [`phases/verify.md`](phases/verify.md) — получить fresh terminal evidence;
- [`phases/reconcile-implementation.md`](phases/reconcile-implementation.md) —
  до staging согласовать явный production set с platform package;
- [`phases/archive.md`](phases/archive.md) — collision-safe архивировать
  implementation change или shared product package;
- [`phases/deep-code-review.md`](phases/deep-code-review.md) — manual-only
  read-only review, feedback triage, bug investigation и harness security audit;
- [`phases/harness-change.md`](phases/harness-change.md) — изменить харнес;
- [`phases/harness-review.md`](phases/harness-review.md) — проверить харнес;
- [`phases/writing-skills.md`](phases/writing-skills.md) — проверить новое
  жёсткое правило, skill или роль через RED → GREEN → REFACTOR.
- [`phases/pre-commit-check.md`](phases/pre-commit-check.md) — проверить уже
  staged index после явного commit intent, не выполняя delivery-действий.

## Правила

- [`rules/specification-layers.md`](rules/specification-layers.md) — общий
  product SSOT и отдельные platform implementation specs;
- [`rules/artifact-language.md`](rules/artifact-language.md) — русский authored
  prose во всех v1 platform artifacts с block-level fail-closed проверкой;
- [`rules/visual-language.md`](rules/visual-language.md) — shared calm soft-blue
  semantic intent и native adaptation boundary;
- [`rules/product-spec-review.md`](rules/product-spec-review.md) — isolated
  six-lens product review, fingerprint и durable receipt gate;
- [`rules/platform-change-lifecycle.md`](rules/platform-change-lifecycle.md) —
  platform package, tier и transitions;
- [`rules/implementation-reconciliation.md`](rules/implementation-reconciliation.md)
  — guarded pre-delivery repair без production/shared writes;
- [`rules/verification-evidence.md`](rules/verification-evidence.md) и
  [`rules/archive-lifecycle.md`](rules/archive-lifecycle.md) — terminal proof и
  dual archive;
- [`rules/system-design.md`](rules/system-design.md) — общая mobile system-design
  база для будущих platform adapters;
- [`rules/system-design/modularity.md`](rules/system-design/modularity.md) —
  v1 strong-default physical capability boundaries, composition-only app shell
  и `isolated | deviation | not-applicable` contract;
- [`compatibility/modularity-v0.json`](compatibility/modularity-v0.json) — exact
  allowlist и immutable hash anchor двух historical v0 identities; меняется
  только отдельным harness change + audit;
- [`rules/coding-standards.md`](rules/coding-standards.md),
  [`rules/tdd-first.md`](rules/tdd-first.md),
  [`rules/test-execution.md`](rules/test-execution.md) и
  [`rules/verification-matrix.md`](rules/verification-matrix.md) — общий
  behavior-first engineering и method-selection baseline;
- [`rules/git-conventions.md`](rules/git-conventions.md),
  [`rules/branching.md`](rules/branching.md) и
  [`rules/developer-experience.md`](rules/developer-experience.md) — условные
  delivery/DX scopes без автоматического commit;
- [`rules/wording-clarity.md`](rules/wording-clarity.md) — cold-readable
  requirements, AC и security формулировки;
- [`rules/orchestration-core.md`](rules/orchestration-core.md) — single-writer,
  bounded loop и no-commit;
- [`rules/memory-architecture.md`](rules/memory-architecture.md) — SSOT и
  граница канон↔адаптер;
- [`rules/platform-scope.md`](rules/platform-scope.md) — common/iOS/Android/
  cross-platform;
- [`rules/code-review.md`](rules/code-review.md),
  [`rules/bug-investigation.md`](rules/bug-investigation.md) и
  [`rules/security-review.md`](rules/security-review.md) — evidence-driven
  review/investigation без исправлений;
- [`rules/runtime-adapters.md`](rules/runtime-adapters.md) — Codex, Claude Code,
  Cursor и OpenCode;
- [`rules/repository-documentation.md`](rules/repository-documentation.md) — три
  root audience layers, SSOT boundary и structural/semantic freshness;
- [`rules/pre-commit-integrity.md`](rules/pre-commit-integrity.md) и
  [`rules/hook-contract.md`](rules/hook-contract.md) — index gate, tracked Git
  hook и единый runtime hook contract;
- [`rules/agent-roster.md`](rules/agent-roster.md) — роли харнеса.

## Роли

- [`roles/implementation-writer.md`](roles/implementation-writer.md) — единый
  контракт writer с harness/platform modes;
- [`roles/harness-auditor.md`](roles/harness-auditor.md) — единый контракт
  read-only аудитора.
- [`roles/repo-navigator.md`](roles/repo-navigator.md),
  [`roles/specification-writer.md`](roles/specification-writer.md),
  [`roles/architecture-designer.md`](roles/architecture-designer.md) и
  [`roles/implementation-planner.md`](roles/implementation-planner.md) — роли
  platform elaboration.
- Platform-owned `ios-ux-designer` / `android-ux-designer` — conditional single
  owners `platform-ux.md` между specification и architecture.
- [`roles/implementation-discovery.md`](roles/implementation-discovery.md) и
  [`roles/verifier.md`](roles/verifier.md) — read-only implementation handoff и
  fresh verification.
- [`roles/product-spec-reviewer.md`](roles/product-spec-reviewer.md) — fresh
  read-only review ровно одной shared product lens.
- [`roles/deep-code-reviewer.md`](roles/deep-code-reviewer.md),
  [`roles/bug-investigator.md`](roles/bug-investigator.md) и
  [`roles/security-reviewer.md`](roles/security-reviewer.md) — read-only роли
  единого deep review.

## Ресурсы

- [`templates/harness-change.md`](templates/harness-change.md) — change-plan;
- [`templates/product-concept.md`](templates/product-concept.md),
  [`templates/product-brief.md`](templates/product-brief.md) и
  [`templates/product-ux.md`](templates/product-ux.md),
  [`templates/product-spec.md`](templates/product-spec.md) — продуктовая
  проработка, UX review и human approval;
- [`templates/product-review-verdict.json`](templates/product-review-verdict.json)
  — exact output schema одного independent lens review;
- [`templates/platform-implementation-spec.md`](templates/platform-implementation-spec.md)
  — downstream спека одного направления;
- [`templates/platform-design.md`](templates/platform-design.md) и
  [`templates/platform-plan-task.md`](templates/platform-plan-task.md) —
  structured modularity decision и task boundary ownership;
- [`templates/platform-ux.md`](templates/platform-ux.md) — conditional native
  UX artifact для product-backed `ui`;
- [`templates/platform-rule-selection.json`](templates/platform-rule-selection.json)
  — immutable planned engineering scope/rule snapshot;
- [`test-evidence/README.md`](test-evidence/README.md) — индекс RED/GREEN,
  runtime и platform evidence;
- [`scripts/harness-lint.py`](scripts/harness-lint.py) — детерминированная
  проверка структуры.
- [`scripts/harness-docs.py`](scripts/harness-docs.py) — exact root docs,
  generated projections, structural freshness и read-only check;
- [`scripts/validate-deep-code-review.py`](scripts/validate-deep-code-review.py),
  [`scripts/read-deep-code-review-report.py`](scripts/read-deep-code-review-report.py),
  [`scripts/deep-code-review-readonly-guard.py`](scripts/deep-code-review-readonly-guard.py)
  и [`scripts/harness-security-audit.py`](scripts/harness-security-audit.py) —
  fail-closed invocation contract, identity-bound report reader, machine
  pre/post mutation guard и bounded redacted security scan;
- [`scripts/find-platform-context.py`](scripts/find-platform-context.py) и
  [`scripts/validate-platform-change.py`](scripts/validate-platform-change.py) —
  profile-aware retrieval и stdlib lifecycle gate;
- [`scripts/validate-product-spec.py`](scripts/validate-product-spec.py) —
  product snapshot/verdict/aggregate/readiness gate;
- [`scripts/platform_rule_profiles.py`](scripts/platform_rule_profiles.py) —
  единый resolver capabilities и phase/scope rule profiles;
- [`scripts/validate-implementation-scope.py`](scripts/validate-implementation-scope.py),
  [`scripts/capture-verification-state.py`](scripts/capture-verification-state.py)
  и [`scripts/archive-change.py`](scripts/archive-change.py) — task scope,
  freshness и collision-safe archive.
- [`scripts/test-watchdog.sh`](scripts/test-watchdog.sh) — bounded запуск
  nontrivial test/build commands.
- [`scripts/workflow-reflection.py`](scripts/workflow-reflection.py) — focused
  propose/plan reflection без legacy paths.
- [`scripts/pre-commit-check.py`](scripts/pre-commit-check.py) и
  [`hooks/hook-runner.py`](hooks/hook-runner.py) — обязательный staged gate и
  ранние runtime guards без дублирования policy.
- [`scripts/reconcile-implementation.py`](scripts/reconcile-implementation.py) —
  explicit-path inspect/start/check guard и implement-mode validation.
- [`scripts/configure-git-hooks.sh`](scripts/configure-git-hooks.sh) — read-only
  `--check` и только явно вызываемый collision-safe `--install` tracked hooks.

Portable skills хранятся в `.agents/skills/`. Runtime-адаптеры хранят только
обнаружение, invocation policy, permissions и binding ролей. Процессное знание
в них не дублировать.
