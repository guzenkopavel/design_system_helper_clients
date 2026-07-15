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
  выбранной платформы; сейчас runtime adapter реализован для iOS;
- [`phases/plan.md`](phases/plan.md) — декомпозировать `specified` package в
  self-contained задачи;
- [`phases/implement.md`](phases/implement.md) — выполнить ready task в
  adapter-owned production scope;
- [`phases/verify.md`](phases/verify.md) — получить fresh terminal evidence;
- [`phases/archive.md`](phases/archive.md) — collision-safe архивировать
  implementation change или shared product package;
- [`phases/harness-change.md`](phases/harness-change.md) — изменить харнес;
- [`phases/harness-review.md`](phases/harness-review.md) — проверить харнес;
- [`phases/writing-skills.md`](phases/writing-skills.md) — проверить новое
  жёсткое правило, skill или роль через RED → GREEN → REFACTOR.

## Правила

- [`rules/specification-layers.md`](rules/specification-layers.md) — общий
  product SSOT и отдельные platform implementation specs;
- [`rules/platform-change-lifecycle.md`](rules/platform-change-lifecycle.md) —
  platform package, tier и transitions;
- [`rules/verification-evidence.md`](rules/verification-evidence.md) и
  [`rules/archive-lifecycle.md`](rules/archive-lifecycle.md) — terminal proof и
  dual archive;
- [`rules/system-design.md`](rules/system-design.md) — общая mobile system-design
  база для будущих platform adapters;
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
- [`rules/runtime-adapters.md`](rules/runtime-adapters.md) — Codex, Claude Code,
  Cursor и OpenCode;
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
- [`roles/implementation-discovery.md`](roles/implementation-discovery.md) и
  [`roles/verifier.md`](roles/verifier.md) — read-only implementation handoff и
  fresh verification.

## Ресурсы

- [`templates/harness-change.md`](templates/harness-change.md) — change-plan;
- [`templates/product-concept.md`](templates/product-concept.md),
  [`templates/product-brief.md`](templates/product-brief.md) и
  [`templates/product-ux.md`](templates/product-ux.md),
  [`templates/product-spec.md`](templates/product-spec.md) — продуктовая
  проработка, UX review и human approval;
- [`templates/platform-implementation-spec.md`](templates/platform-implementation-spec.md)
  — downstream спека одного направления;
- [`templates/platform-rule-selection.json`](templates/platform-rule-selection.json)
  — immutable planned engineering scope/rule snapshot;
- [`test-evidence/README.md`](test-evidence/README.md) — индекс RED/GREEN,
  runtime и platform evidence;
- [`scripts/harness-lint.py`](scripts/harness-lint.py) — детерминированная
  проверка структуры.
- [`scripts/find-platform-context.py`](scripts/find-platform-context.py) и
  [`scripts/validate-platform-change.py`](scripts/validate-platform-change.py) —
  profile-aware retrieval и stdlib lifecycle gate;
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

Portable skills хранятся в `.agents/skills/`. Runtime-адаптеры хранят только
обнаружение, invocation policy, permissions и binding ролей. Процессное знание
в них не дублировать.
