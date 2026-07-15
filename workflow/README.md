# Workflow

Канонический, независимый от runtime слой процесса.

## Фазы

- [`phases/brainstorming.md`](phases/brainstorming.md) — исследовать сырую
  продуктовую идею и реальные альтернативы;
- [`phases/discovery.md`](phases/discovery.md) — собрать общий product brief для
  iOS и Android;
- [`phases/elaborate.md`](phases/elaborate.md) — довести общий продуктовый пакет
  до `READY` и остановиться до platform fan-out;
- [`phases/harness-change.md`](phases/harness-change.md) — изменить харнес;
- [`phases/harness-review.md`](phases/harness-review.md) — проверить харнес;
- [`phases/writing-skills.md`](phases/writing-skills.md) — проверить новое
  жёсткое правило, skill или роль через RED → GREEN → REFACTOR.

## Правила

- [`rules/specification-layers.md`](rules/specification-layers.md) — общий
  product SSOT и отдельные platform implementation specs;
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
  контракт writer;
- [`roles/harness-auditor.md`](roles/harness-auditor.md) — единый контракт
  read-only аудитора.

## Ресурсы

- [`templates/harness-change.md`](templates/harness-change.md) — change-plan;
- [`templates/product-concept.md`](templates/product-concept.md),
  [`templates/product-brief.md`](templates/product-brief.md) и
  [`templates/product-ux.md`](templates/product-ux.md),
  [`templates/product-spec.md`](templates/product-spec.md) — продуктовая
  проработка, UX review и human approval;
- [`templates/platform-implementation-spec.md`](templates/platform-implementation-spec.md)
  — downstream спека одного направления;
- [`test-evidence/README.md`](test-evidence/README.md) — индекс RED/GREEN,
  runtime и platform evidence;
- [`scripts/harness-lint.py`](scripts/harness-lint.py) — детерминированная
  проверка структуры.

Portable skills хранятся в `.agents/skills/`. Runtime-адаптеры хранят только
обнаружение, invocation policy, permissions и binding ролей. Процессное знание
в них не дублировать.
