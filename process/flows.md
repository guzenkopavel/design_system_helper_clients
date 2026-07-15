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
