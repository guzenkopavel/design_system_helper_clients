# Harness flows

```text
request
  → harness-change intake
  → common | ios | android | cross-platform scope
  → locate canonical owner
  → implementation-writer
  → wiring cascade
  → README/workflow/deep-info impact dispositions
  → harness-docs render + read-only check
  → harness-lint + harness-auditor semantic docs review
  → fix-loop
  → grade A + CLEAN
```

Root docs — производная проекция. Structural checker обновляет только marked
blocks; auditor отдельно проверяет audience layering, ownership, invocation и
iOS/Android claims. Новый skill/role/runtime wrapper для documentation flow не
нужен: существующие `harness-change` и `harness-review` владеют маршрутом.

При `cross-platform` ветка review делится на независимые iOS и Android evidence,
затем снова объединяется в общий verdict.

Runtime выбирает только способ обнаружения skill и вызова роли. Канонический
flow не меняется между Codex, Claude Code, Cursor и OpenCode.

## Explicit commit flow

```text
explicit commit intent
  → explicit intended path set
  → reconcile-implementation per platform/feature/change identity
  → reconciliation report
  → scoped staging of approved set
  → pre-commit-check over staged index + exact intended path binding
  → platform profile + task/evidence trail + harness lint when applicable
  → stable staged fingerprint: PASS + private short-lived receipt
  → runtime hook previews receipt without consumption
  → tracked Git hook consumes receipt one-shot and reruns integrity
  → commit under the original explicit authorization
```

Runtime hooks дают ранние deny/warnings для опасных команд и edits, но не stage,
commit, push и не заменяют tracked Git hook. Изменение index инвалидирует receipt.
Hook/gate только подсказывают reconciliation для uncovered production trail и
никогда не запускают repair автоматически.
Unrelated unstaged state не входит в delivery lane. Extra/missing staged path,
неполная rename/copy identity или ambiguous active package owner mutable path
блокируют commit; copy source остаётся explicit guarded read-only peer.
Generic hook без свежего receipt не авторизует commit; exact intended binding
принадлежит coordinator gate до commit, tracked hook потребляет receipt one-shot.

## Product elaboration

```text
raw idea
  → read specs/product/<feature>/SPECIFICATION.md when present (current baseline)
  → brainstorming (optional, alternatives)
  → discovery (shared brief + draft REQ/AC + screen/flow impact)
  → elaborate candidate DRAFT + shared UX
  → isolated review/fix cycles
  → explicit human approval (fingerprint changes)
  → final snapshot
  → coordinator creates six fresh contexts and retains runtime invocation evidence
  → six product-spec-reviewer verdict attestations (one lens each, one parent session)
  → coordinator aggregate PASS or durable GAPS/UNKNOWN review-verdicts.json
  → Status READY + Readiness Decision READY/none + validate-product-spec.py check
  → shared product spec: READY
  → STOP
  → iOS implementation spec and/or Android implementation spec (separate flow)
```

Общий active package принадлежит `specs/product/<feature>/`; долговечный
`SPECIFICATION.md` в том же feature root остаётся read-only current baseline и
не входит в review fingerprint. После `READY` каждое
направление создаёт собственную implementation spec внутри своего корня и
ссылается на общий контракт, не копируя его.

Без явного human product approval, полного REQ↔AC coverage, applicable UX,
fresh exact-six receipt и закрытых blockers flow остаётся в `DRAFT` до fan-out.
Terminal READY также требует PASS Client Readiness как полноту shared contract
и отдельную unique verification dimension для каждого атомарного AC.
Same-context/no-subagent fallback даёт durable `UNKNOWN`, не independent PASS;
repo validator проверяет attestation/schema/freshness, а не доказывает runtime isolation.

Техническая platform-only ветка может обойти product elaboration только через
intake `technical-only`: `Product impact assessment: NONE` и evidence, что
observable behavior, REQ и AC не меняются. `PRESENT` или `UNCERTAIN` возвращают
задачу в product flow.

## Platform implementation lifecycle

```text
propose <platform> <feature> [--change <change-id>]
  → read feature-root SPECIFICATION.md when present
  → current modularity contract v1 (legacy v0 cannot enter Propose)
  → platform/intake gate
  → repo-navigator (read-only)
  → evidence-selected engineering scopes + exact propose profile
  → specification-writer
  → product-backed ui only: adapter UX designer writes platform-ux.md
  → architecture-designer (consumes platform-ux.md only when present)
  → structured isolated | deviation | not-applicable modularity decision
  → Russian authored prose block gate; exact schema/IDs/paths/code stay unchanged
  → platform boundary guard (read-only PASS/BLOCK; missing/BLOCK stops design gate)
  → validator
  → status: specified
plan <platform> <feature> [--change <change-id>]
  → revalidate/refine scopes + exact plan profile
  → implementation-planner
  → writable production Paths + immutable Read-only context
  → current v1 task Implementation deliverables: что будет реализовано
  → separate Steps: как реализовать; Expected result: доказанный итог
  → adapter boundary/classification/overlap gate in mode=plan
  → physical-unit/project wiring + public API/consumer/app-shell tasks with boundary owners
  → seal plan/rule-selection.json
  → task/DAG validator
  → status: planned
implement <platform> <feature> [--change <change-id>] [--task ...|--all]
  → v1 sealed contract OR exact registry-anchored v0 historical projection
  → implementation-discovery (read-only)
  → exact implement profile + immutable scopes
  → schema v3 scoped lane baseline; disjoint dirty/index/commit допускаются
  → implementation-writer (platform-implementation)
  → v1: sealed modularity outcome and composition-only app shell
  → v0: historical task/check completion only; no ownership/structure expansion
  → bounded focused evidence + scope check
  → status: implementing
verify <platform> <feature> [--change <change-id>]
  → verify scoped lane baseline over package + realized Paths + read dependencies
  → verifier (production read-only)
  → v1 realized graph/API/module/consumer/app-shell checks OR anchored v0 legacy checks
  → v1 product-backed ui exact NATIVE-* rows + structured observation records
  → exact verify profile + independently derived method matrix
  → verify production-scope check
  → exact PASS evidence + state fingerprint
  → status: verified
archive implementation ...
  → dry-run → collision-safe apply → publish current SPECIFICATION.md → tombstone
```

Перед delivery явный production set может пройти
`reconcile-implementation <platform> <feature> [--change ...] --path ...`.
`aligned`/`task-drift`/`platform-implementation-drift` обрабатываются внутри
guard; shared behavior present/uncertain возвращается в product elaboration.
Каждая platform/feature/change identity получает отдельный запуск: это касается
и cross-platform set, и двух packages одной платформы.
Явный `--change` выбирает одну lane при нескольких active packages; omission с
ambiguity/partial sibling блокируется. Guards допускают disjoint platform/
feature/product changes и unrelated commit, но selected package/Paths/shared
spec/rules/adapter/control-plane drift остаётся invalid.

Product archive — отдельная ветка с retirement approval, platform dispositions
и active-reference scan. Default request находится в `_retirement-requests`
вне active fingerprint; apply сохраняет validated copy внутри product archive.
`completed` публикует approved current `SPECIFICATION.md`, а
`superseded`/`cancelled` сохраняет прежний baseline без продвижения candidate.
Каждый implementation шаг проверяет adapter capability.
iOS и Android проходят один общий lifecycle; platform addenda независимо
выбирают commands/infrastructure и не являются доказательством друг для друга.

## Manual deep code review

```text
deep-code-review review|feedback|bug <platform> <feature> [--change ...]
  → fail-closed identity/path validation
  → common read-only role + platform addendum
  → evidence-backed DCR findings
  → No edits made
  → explicit lifecycle route only when a later fix is requested

deep-code-review security [--json]
  → redacted deterministic scan
  → contextual validation by security-reviewer
  → PASS | findings | UNKNOWN when scanner unavailable
```

Этот flow не меняет production/package/evidence и не запускает lifecycle.
Android review остаётся платформенным и после отдельного fix возвращает route
`verify android`; сам review не заявляет fixed/verified.
