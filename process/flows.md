# Harness flows

```text
request
  → harness-change intake
  → common | ios | android | cross-platform scope
  → locate canonical owner
  → implementation-writer
  → wiring cascade
  → harness-lint + harness-auditor
  → fix-loop
  → grade A + CLEAN
```

При `cross-platform` ветка review делится на независимые iOS и Android evidence,
затем снова объединяется в общий verdict.

Runtime выбирает только способ обнаружения skill и вызова роли. Канонический
flow не меняется между Codex, Claude Code, Cursor и OpenCode.

## Product elaboration

```text
raw idea
  → brainstorming (optional, alternatives)
  → discovery (shared brief + draft REQ/AC + screen/flow impact)
  → elaborate (shared UX when applicable + review lenses + human approval)
  → shared product spec: READY
  → STOP
  → iOS implementation spec and/or Android implementation spec (separate flow)
```

Общий пакет принадлежит `specs/product/<feature>/`. После `READY` каждое
направление создаёт собственную implementation spec внутри своего корня и
ссылается на общий контракт, не копируя его.

Без явного human product approval, полного REQ↔AC coverage, applicable UX
artifact/reviews и закрытых blockers flow остаётся в `DRAFT` до fan-out.

Техническая platform-only ветка может обойти product elaboration только через
intake `technical-only`: `Product impact assessment: NONE` и evidence, что
observable behavior, REQ и AC не меняются. `PRESENT` или `UNCERTAIN` возвращают
задачу в product flow.

## Platform implementation lifecycle

```text
propose <platform> <feature> [--change <change-id>]
  → platform/intake gate
  → repo-navigator (read-only)
  → evidence-selected engineering scopes + exact propose profile
  → specification-writer
  → architecture-designer when required
  → platform boundary guard (read-only)
  → validator
  → status: specified
plan <platform> <feature> [--change <change-id>]
  → revalidate/refine scopes + exact plan profile
  → implementation-planner
  → seal plan/rule-selection.json
  → task/DAG validator
  → status: planned
implement <platform> <feature> [--change <change-id>] [--task ...|--all]
  → implementation-discovery (read-only)
  → exact implement profile + immutable scopes
  → scope baseline
  → implementation-writer (platform-implementation)
  → bounded focused evidence + scope check
  → status: implementing
verify <platform> <feature> [--change <change-id>]
  → verify production-scope baseline
  → verifier (production read-only)
  → exact verify profile + independently derived method matrix
  → verify production-scope check
  → exact PASS evidence + state fingerprint
  → status: verified
archive implementation ...
  → dry-run → collision-safe apply → tombstone
```

Product archive — отдельная ветка с retirement approval, platform dispositions
и active-reference scan. Сейчас implementation dispatch существует только для
iOS. Android использует общий lifecycle как future foundation, но любой
implementation вызов блокируется до создания artifacts.
