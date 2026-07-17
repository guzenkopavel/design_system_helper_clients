# Полная карта харнеса

Этот документ — простой, но полный wiring reference. Он помогает ответить на
вопросы «откуда пришло правило», «кто имеет право писать артефакт» и «какой
validator подтверждает результат». Это объясняющая проекция: при расхождении
канон из [`workflow/`](workflow/), platform contract/addendum или
[`process/`](process/) имеет приоритет.

## Ментальная модель

```text
runtime
  → portable skill
  → common phase
  → common roles / scripts / templates
  → platform adapter capability + phase/scope profile
  → platform addendum / rules / roles
  → product or platform artifacts
  → validators
  → focused and terminal evidence
```

Runtime отвечает только за discovery, явный invocation, permissions, role и
hook binding. Portable skill даёт короткий стабильный entrypoint. Common phase
владеет последовательностью действий. Adapter разрешает capability, задаёт
ownership roots и выбирает применимые rule profiles. Platform addendum содержит
только реальные различия SDK/tooling. Артефакты и evidence принимаются
валидаторами, а не narrative агента.

Physical modularity v1 — обязательная base-семантика, не optional scope. Common
SSOT находится в `workflow/rules/system-design/modularity.md`; adapter добавляет
`modularity.isolation_scope`, platform rule и допустимые physical units. Все
четыре phase profiles включают common+platform pair. `design.md` хранит exact
`isolated | deviation | not-applicable` decision и `PASS` boundary guard;
validator проверяет структуру, а semantic quality evidence остаётся
ответственностью guard/auditor.
Legacy v0 разрешается только общим resolver при exact match tracked
`workflow/compatibility/modularity-v0.json`: full design/rule-selection/plan
hashes, immutable meta projection и normalized task graph. Нормализация
игнорирует только значения task Status/Evidence; historical package не получает
ретроактивный v1 composition verdict и не может расширять ownership/structure.
Resolver также pin'ит canonical registry digest и ordered exact two identities,
а legacy meta принимает exact key set: mutable только status/tasks_done/problems/
verification fields. Registry-only append, extra key и `blocking_questions`
drift fail-closed.

Язык v1 platform artifacts — такая же обязательная base-семантика. Common SSOT
находится в `workflow/rules/artifact-language.md`; оба adapter catalog включают
его во все `phase_rule_profiles`. `specification-writer`, platform UX designer,
`architecture-designer`, `implementation-planner` и `verifier` создают русский
authored prose, а exact schema/IDs/paths/code/API terms не переводят.
`validate-platform-change.py` удаляет code fences, inline code, URLs, paths,
contract IDs и machine rows, после чего проверяет каждый остаточный prose block
на meaningful Cyrillic и Cyrillic dominance. Диагностика ограничена одной
строкой на файл и не раскрывает content. `plan/` проверяется с Plan, raw command
logs/evidence не используются как authored padding. Resolver удаляет правило из
registry-anchored v0 projection, чтобы historical hashes оставались валидны.
Direct-child `evidence/task-NNN.md` имеет специализированный typed contract:
обязательный содержательный русский summary и raw technical section
`Технические доказательства` с exact legacy alias `Changed paths`; exact names
распознаются на H1/H2, хотя canonical template остаётся H2. Specialized helper
построчно исключает только safe repo-relative path/change rows с finite
technical annotation. Bounded repo-tooling commands допускаются без fence лишь
в canonical разделе и требуют finite option names и safe structured values.
Fenced verbatim output игнорируется общим parser, произвольный unfenced output и
все остальные строки проходят authored gate. Raw inventory ненормативен:
outcome, решения и ограничения в нём недопустимы. Report без русского summary
или с mixed duplicate summary блокируется.
Canonical timestamped
`evidence/reconciliation-...-task-NNN[-slug].md` целиком остаётся authored и не
получает task exemption.
Validator не делает rglob: произвольные runtime/verifier Markdown, logs,
screenshots, JSON и external output остаются raw, не требуют перевода и не могут
маскировать English authored report. Typed reports проходят ту же package
containment/all-component symlink/regular/strict UTF-8 boundary во всех current
v1 validator modes; v0 остаётся exempt.

Product READY имеет отдельный durable trust boundary. Elaborate fingerprint'ит
все regular files активного package (кроме coordinator receipt; только exact
Status metadata нормализуется), затем запускает шесть one-lens fresh
`product-spec-reviewer` contexts. Reviewer read-only и не видит writer rationale
или другие verdicts. Coordinator агрегирует `review-verdicts.json`; platform
product-backed intake и completed product archive вызывают тот же
`validate-product-spec.py check`.

<!-- BEGIN GENERATED: DEEP_WIRING -->
### Skill call graph

| Skill | Common phase | Recommended roles | Artifact contract |
|---|---|---|---|
| `archive` | [`workflow/phases/archive.md`](workflow/phases/archive.md) | — | `platform archive package, durable SPECIFICATION.md and ARCHIVED.md tombstone`, `product archive package, durable SPECIFICATION.md and spec.md tombstone` |
| `brainstorming` | [`workflow/phases/brainstorming.md`](workflow/phases/brainstorming.md) | — | `specs/product/<feature>/concept.md (optional)` |
| `deep-code-review` | [`workflow/phases/deep-code-review.md`](workflow/phases/deep-code-review.md) | `deep-code-reviewer`, `bug-investigator`, `security-reviewer` | read-only |
| `discovery` | [`workflow/phases/discovery.md`](workflow/phases/discovery.md) | — | `specs/product/<feature>/brief.md` |
| `elaborate` | [`workflow/phases/elaborate.md`](workflow/phases/elaborate.md) | `product-spec-reviewer` | `specs/product/<feature>/brief.md`, `specs/product/<feature>/ux.md (UI/interaction only)`, `specs/product/<feature>/spec.md`, `specs/product/<feature>/review-verdicts.json` |
| `harness-change` | [`workflow/phases/harness-change.md`](workflow/phases/harness-change.md) | `implementation-writer`, `harness-auditor` | `canonical harness files`, `synchronized runtime adapters and process map`, `workflow/test-evidence/<name>.md for hard changes` |
| `harness-review` | [`workflow/phases/harness-review.md`](workflow/phases/harness-review.md) | `harness-auditor`, `implementation-writer` | read-only |
| `implement` | [`workflow/phases/implement.md`](workflow/phases/implement.md) | `implementation-discovery`, `implementation-writer` | `task-declared production paths`, `<platform>/specs/<feature>/changes/<change-id>/evidence/task-NNN.md`, `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md` |
| `plan` | [`workflow/phases/plan.md`](workflow/phases/plan.md) | `repo-navigator`, `implementation-planner` | `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/README.md`, `<platform>/specs/<feature>/changes/<change-id>/plan/rule-selection.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md` |
| `pre-commit-check` | [`workflow/phases/pre-commit-check.md`](workflow/phases/pre-commit-check.md) | — | read-only |
| `propose` | [`workflow/phases/propose.md`](workflow/phases/propose.md) | `repo-navigator`, `specification-writer`, `adapter-selected platform UX designer (product-backed ui only)`, `architecture-designer` | `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/proposal.md`, `<platform>/specs/<feature>/changes/<change-id>/implementation-spec.md`, `<platform>/specs/<feature>/changes/<change-id>/design.md`, `<platform>/specs/<feature>/changes/<change-id>/verification.md`, `<platform>/specs/<feature>/changes/<change-id>/platform-ux.md (product-backed ui only)` |
| `reconcile-implementation` | [`workflow/phases/reconcile-implementation.md`](workflow/phases/reconcile-implementation.md) | `implementation-discovery`, `specification-writer`, `architecture-designer`, `implementation-planner`, `implementation-writer` | `<platform>/specs/<feature>/changes/<change-id>/implementation-spec.md`, `<platform>/specs/<feature>/changes/<change-id>/design.md`, `<platform>/specs/<feature>/changes/<change-id>/verification.md`, `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/`, `<platform>/specs/<feature>/changes/<change-id>/evidence/reconciliation-*.md` |
| `verify` | [`workflow/phases/verify.md`](workflow/phases/verify.md) | `verifier` | `<platform>/specs/<feature>/changes/<change-id>/verification.md`, `<platform>/specs/<feature>/changes/<change-id>/evidence/`, `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md (recovery only)` |
| `writing-skills` | [`workflow/phases/writing-skills.md`](workflow/phases/writing-skills.md) | `implementation-writer`, `harness-auditor` | `workflow/test-evidence/<name>.md` |

### Platform adapter projection

| Platform | Adapter | Capabilities | Phase profiles | Scope profiles | Addenda | Rules | Roles |
|---|---|---|---:|---:|---:|---:|---:|
| iOS | [`iOS/workflow/platform-contract.json`](iOS/workflow/platform-contract.json) | propose, plan, implement, verify, archive-implementation | 4 | 14 | 8 | 30 | 2 |
| Android | [`Android/workflow/platform-contract.json`](Android/workflow/platform-contract.json) | propose, plan, implement, verify, archive-implementation | 4 | 10 | 8 | 18 | 4 |
<!-- END GENERATED: DEEP_WIRING -->

## Ownership и SSOT

| Knowledge | Канонический владелец | Производные поверхности |
|---|---|---|
| Общий lifecycle и policy | [`workflow/phases/`](workflow/phases/), [`workflow/rules/`](workflow/rules/) | portable skills, root docs, runtime commands |
| Общие роли | [`workflow/roles/`](workflow/roles/) | четыре runtime role bindings |
| Platform capability/profile | `<platform>/workflow/platform-contract.json` | capability matrices и lifecycle dispatch |
| Physical modularity | [`workflow/rules/system-design/modularity.md`](workflow/rules/system-design/modularity.md) + adapter `modularity` + platform rule | structured design decision, task checks, lint/validator gates |
| Язык platform artifacts | [`workflow/rules/artifact-language.md`](workflow/rules/artifact-language.md) + оба adapter phase profiles | русские authored blocks, role/template instructions, fail-closed validator/lint |
| Modularity v0 compatibility | [`workflow/compatibility/modularity-v0.json`](workflow/compatibility/modularity-v0.json) + common resolver | exact historical identities, immutable hashes, downstream fail-closed gates |
| Platform-specific behavior | `<platform>/workflow/phases/`, `rules/`, `roles/` | runtime platform roles и evidence |
| Product contract | [`specs/product/`](specs/product/) | active package + feature-root durable `SPECIFICATION.md` baseline |
| Platform implementation | `<platform>/specs/` и adapter-owned production root | plan, code, evidence, archive + durable platform baseline |
| Связи сущностей | [`process/`](process/) | навигация; не policy copy |
| Portable invocation | [`.agents/skills/`](.agents/skills/) | Claude Code/OpenCode commands, native discovery |
| Root documentation | [`README.md`](README.md), [`workflow.md`](workflow.md), этот файл | generated structural projections |

Root docs не владеют lifecycle rules. Manual prose объясняет смысл, generated
blocks фиксируют структурный graph. Семантическое изменение правила требует
осознанной проверки prose; простое редактирование generated block запрещено.

## Product package schema

```text
specs/product/<feature>/
  SPECIFICATION.md # current delivered baseline; excluded from active fingerprint
  concept.md       # problem, outcome, alternatives
  brief.md         # users, scope, draft requirements and screen/flow impact
  ux.md            # shared UX only when UI/interaction applies
  spec.md          # READY/APPROVED atomic REQ↔AC + exact readiness decision
  review-verdicts.json # exact-six PASS/GAPS/UNKNOWN findings/verdict receipt

specs/product/_retirement-requests/<feature>/<date-feature>.json
                  # default request вне active review fingerprint

specs/product/_archive/<feature>/<archive-id>/
  retirement-request.json # durable validated retirement evidence
  ...              # moved retired product package; product receipt не создаётся
```

Состояние до approval — `DRAFT / PENDING APPROVAL`. `elaborate` может перевести
package в `READY` только с явным human evidence, закрытыми blockers, полным
coverage, уникальными metadata/REQ/AC и PASS reviews. Verdict provenance —
проверяемая attestation; реальную isolation обеспечивает coordinator/runtime и
его invocation evidence. Product archive — отдельная операция: она
требует retirement approval и dispositions всех platform implementations. Она
перемещает полный product package, оставляет `spec.md` tombstone и для
`completed` публикует approved `SPECIFICATION.md`; cancelled/superseded
сохраняют прежний baseline. `archive-receipt.json` создаёт platform
implementation archive и explicit implementation retirement; только verified
implementation archive receipts доказывают archived dispositions, retirement
receipts лишь классифицируют tombstone и снимают active ownership.
Client Readiness проверяет полноту shared contract, не downstream status;
каждый AC имеет одну уникальную verification dimension. Product/platform prose
и authored JSON reports проходят общий sentence-level language helper; platform
meta JSON и structured native obligations применяются только к current v1.
Registry-anchored v0 завершает historical exact-hash checks без retrofit.

## Platform package schema и состояния

```text
<platform>/specs/<feature>/changes/<change-id>/
  meta.json
  proposal.md
  implementation-spec.md
  platform-ux.md   # conditional product-backed ui native UX contract
  design.md
  verification.md
  plan/
    README.md
    task-001.md     # writable Paths + immutable Read-only context
    rule-selection.json
  evidence/
    ...
    verification-state.json

<platform>/specs/<feature>/archive/<date-change-id>/
  archive-receipt.json
  ...

<platform>/specs/<feature>/SPECIFICATION.md
  # current verified full platform contract; archived source/receipt provenance
  # explicit implementation retirement never publishes this baseline
```

```text
draft → specified → planned → implementing → verified → archived
```

`meta.json` хранит identity, intake type, product link/impact, tier, immutable
engineering scopes после Plan, exact `applicable_rule_files`, task counters,
problems и verification state. `plan/rule-selection.json` запечатывает scopes,
exact `applicable_rule_files` и fingerprint только этих двух полей.
Implementation/Verify scope baselines имеют schema version 3 и algorithm
`git-visible-lane-v1`: fingerprint включает tracked + non-ignored untracked
files selected package, task/realized Paths, Read-only context, shared spec,
rules, adapter и control plane, но исключает ignored caches/build output и
disjoint identities. Exact index projection `git-ls-files-stage-lane-v1` хранит
для каждого watched path mode, stage и blob ID. Global HEAD не является lock:
unrelated commit допустим, selected projection drift блокируется.
Implement не интерпретирует общий `git status` после green selected-lane
snapshot: foreign/disjoint platform, feature или product state остаётся вне
задачи. `INVALID` блокирует writes exact lane diagnostics и не разрешает
переписывать evidence предыдущей задачи. После writer/focused checks canonical
scope check использует coordinator-held snapshot SHA; typed report следует
[`platform-task-evidence.md`](workflow/templates/platform-task-evidence.md).
Для product-backed `ui` adapter `platform_ux` также запечатывает role/artifact,
native design language, required terms и task checks в semantic projection;
сам artifact входит в terminal state fingerprint. Technical-only/non-UI ветки
не требуют его.
Tasks образуют DAG, называют точные writable production `Paths`, immutable
`Read-only context`, Inline contract context и focused evidence. Mode=plan
проверяет adapter boundaries, classification, duplicates и ancestor overlaps.
Current v1 task между Inline contract context и Steps содержит exact
`Implementation deliverables` с минимум двумя substantive top-level list items:
это отдельный список реализуемых artifacts/behavior/boundaries/tests/config
outcomes, а не prose-дубль Steps. Registry-anchored v0 не ретрофитится.
После stripping технических tokens единый NFKC/casefold tokenizer удаляет
оставшиеся `Mn`/`Me`/`Cf`, требует 4 alphabetic words и 24 letters, считает
hyphen/apostrophe word одним token и блокирует one-letter punctuation chains и
mixed Cyrillic/Latin lookalikes внутри одного prose token.
Один canonical ownership helper применяется в Plan/Implement/Reconcile/
pre-commit и запрещает symlink traversal для existing file, directory boundary
и proposed child. Любой direct child active namespace классифицируется как
active package, exact tombstone-only либо partial/unclassified; explicit
`--change` изолирует корректный package, omission при junk sibling блокируется.
Каждая task также называет boundary owner; isolation tasks материализуют
physical-unit wiring, minimal API/visibility, consumer integration/build,
dependency graph и composition-only application shell.
Для v1 semantic adapter projection не хранится в plan snapshot: она вычисляется и
хешируется внутри `verification-state.json` вместе с selected profile semantics.
Для anchored v0 resolver сначала сверяет registry hashes и только затем строит
historical projection с adapter `legacy_task_checks`.

`verification.md` содержит строки каждого active contract с методом, expected
evidence и точным `PASS|FAIL|UNKNOWN`. Non-PASS возвращает затронутые tasks и их
dependent closure в recovery. `verification-state.json` хеширует realized task
paths, package contracts/evidence, selected semantic profiles и обязательные
common/platform terminal contracts. Изменение входа делает fingerprint stale и
блокирует archive до нового Verify.

## Hooks, security и write boundaries

Runtime hooks передают события в
[`workflow/hooks/hook-runner.py`](workflow/hooks/hook-runner.py), который
применяет единый Git/secret/scope policy. Bindings не копируют policy. Tracked
[`.githooks/pre-commit`](.githooks/pre-commit) запускает обязательный staged
gate; [`workflow/scripts/configure-git-hooks.sh`](workflow/scripts/configure-git-hooks.sh)
имеет read-only check и только явный install.

`pre-commit-check.py` читает staged snapshot, проверяет secrets/generated
artifacts, platform profile, task/evidence trail и при необходимости harness
lint. Coordinator invocation дополнительно требует exact intended `--path` set,
обе стороны rename/copy и unique active package owner для mutable paths;
rename old/new mutable, copy destination mutable, а explicit byte-equal
unchanged source является guarded read-only peer. Extra/missing staged path
даёт FAIL. Copy source дополнительно требует exact HEAD/index/worktree
mode/blob, единственную stage-0 entry и отсутствие staged/unstaged/unmerged
delta; unrelated unstaged state вне lane допустим. Exact PASS создаёт private `0700`/
`0600` short-lived receipt с repo/index/path binding. Runtime hook проверяет его
без consumption, tracked `--hook` атомарно потребляет one-shot; absent/stale/
malformed/replay дают FAIL. Gate не stage/commit/push. `deep-code-review`
оборачивается private ephemeral
mutation guard. `harness-security-audit.py` выполняет bounded redacted scan и
fail-closed сообщает incomplete coverage. Terminal Verify запрещает production
writes, а Implement ограничен paths текущего task.

`reconcile-implementation.py` до staging связывает только явный intended
production set с одной platform/feature/change identity. Каждый package получает
собственный guard/report; uncovered adapter-owned path добавляется в coherent
task/plan, а unsafe/mixed/cross-package ownership route блокируется. Private
guard сохраняет scoped index, production, shared/proposal/rules и historical
evidence selected lane; disjoint dirty/index/commit другой identity не блокирует;
per-class meta allowlist сохраняет identity/intake/product authority.
Post-archive verified receipt допускает package-level delivery coverage с
warnings, когда exact archived task/verified scope уже финального set.
После package repair запускается implement-mode validator. Hook/gate не вызывают
repair и могут дать только hint. FAIL/UNKNOWN маршрутизируется в Implement
recovery до guard; verified invalidation требует свежий Verify только для
восстановления terminal claim.

## Reverse lookup

Если вы начинаете с…

- skill name — откройте `.agents/skills/<name>/SKILL.md`, затем указанную
  `workflow/phases/<name>.md`;
- runtime command — найдите thin command, затем portable skill; procedure в
  command отсутствует;
- role — найдите canonical contract в `workflow/roles/` или platform `roles/`,
  затем одноимённые bindings четырёх runtime;
- platform operation — проверьте capability в `platform-contract.json`, phase
  profile, common phase и platform addendum;
- package artifact — найдите owner phase, validator и evidence contract;
- lint finding — найдите check function в `workflow/scripts/harness-lint.py`,
  затем каноническое rule/phase, которое этот check защищает;
- неизвестный файл — используйте generated inventory ниже: он включает все
  объявленные harness surfaces, но не transient packages и native source.

## Call graphs

```text
product-backed:
runtime → brainstorming? → discovery → elaborate candidate/approval
        → six fresh one-lens reviews → receipt → READY/check
        → platform fan-out → propose → plan → implement → verify → archive

technical-only:
impact evidence NONE → propose --technical-only → plan → implement → verify

harness change:
harness-change intake → single writer → docs render/check → harness lint
                     → read-only harness auditor → bounded fix-loop

explicit commit:
user intent → explicit paths → reconcile per platform/feature/change → report
            → scoped stage → exact-intended pre-commit-check
            → receipt preview → tracked one-shot consumption/integrity → commit
```

## Полный file inventory

Inventory строится только из harness roots, root entrypoints, runtime configs,
platform workflow и notices. Он намеренно исключает `.git`, caches/build output,
native product/source, transient `specs/` packages и тела third-party лицензий.
Добавление, удаление или перемещение harness surface делает блок stale.

<!-- BEGIN GENERATED: DEEP_INVENTORY -->
### Android harness

| Path | Purpose |
|---|---|
| [`Android/workflow/README.md`](Android/workflow/README.md) | Android workflow |
| [`Android/workflow/phases/archive.md`](Android/workflow/phases/archive.md) | Android addendum: Implementation Archive |
| [`Android/workflow/phases/deep-code-review.md`](Android/workflow/phases/deep-code-review.md) | Android addendum: Deep Code Review |
| [`Android/workflow/phases/implement.md`](Android/workflow/phases/implement.md) | Android addendum: Implement |
| [`Android/workflow/phases/plan.md`](Android/workflow/phases/plan.md) | Android addendum: Plan |
| [`Android/workflow/phases/pre-commit-check.md`](Android/workflow/phases/pre-commit-check.md) | Android addendum: Pre-commit Check |
| [`Android/workflow/phases/propose.md`](Android/workflow/phases/propose.md) | Android addendum: Propose |
| [`Android/workflow/phases/reconcile-implementation.md`](Android/workflow/phases/reconcile-implementation.md) | Android addendum: Reconcile Implementation |
| [`Android/workflow/phases/verify.md`](Android/workflow/phases/verify.md) | Android addendum: Verify |
| [`Android/workflow/platform-contract.json`](Android/workflow/platform-contract.json) | Capability, profile и ownership contract платформы |
| [`Android/workflow/roles/android-build-diagnostician.md`](Android/workflow/roles/android-build-diagnostician.md) | Android build diagnostician |
| [`Android/workflow/roles/android-kotlin-reviewer.md`](Android/workflow/roles/android-kotlin-reviewer.md) | Android Kotlin reviewer |
| [`Android/workflow/roles/android-package-boundary-guard.md`](Android/workflow/roles/android-package-boundary-guard.md) | Android package boundary guard |
| [`Android/workflow/roles/android-ux-designer.md`](Android/workflow/roles/android-ux-designer.md) | Role: Android UX Designer |
| [`Android/workflow/rules/accessibility.md`](Android/workflow/rules/accessibility.md) | Android accessibility |
| [`Android/workflow/rules/android-pitfalls.md`](Android/workflow/rules/android-pitfalls.md) | Android pitfalls |
| [`Android/workflow/rules/architecture.md`](Android/workflow/rules/architecture.md) | Android architecture |
| [`Android/workflow/rules/architecture/data-layer.md`](Android/workflow/rules/architecture/data-layer.md) | Data layer |
| [`Android/workflow/rules/architecture/dependency-injection.md`](Android/workflow/rules/architecture/dependency-injection.md) | Dependency injection |
| [`Android/workflow/rules/architecture/domain-layer.md`](Android/workflow/rules/architecture/domain-layer.md) | Domain layer |
| [`Android/workflow/rules/architecture/modularization.md`](Android/workflow/rules/architecture/modularization.md) | Android modularization |
| [`Android/workflow/rules/architecture/ui-layer.md`](Android/workflow/rules/architecture/ui-layer.md) | UI layer |
| [`Android/workflow/rules/compose.md`](Android/workflow/rules/compose.md) | Compose |
| [`Android/workflow/rules/coroutines-flows.md`](Android/workflow/rules/coroutines-flows.md) | Coroutines and Flow |
| [`Android/workflow/rules/emulator.md`](Android/workflow/rules/emulator.md) | Emulator |
| [`Android/workflow/rules/gradle-build.md`](Android/workflow/rules/gradle-build.md) | Gradle build |
| [`Android/workflow/rules/kotlin-style.md`](Android/workflow/rules/kotlin-style.md) | Kotlin style |
| [`Android/workflow/rules/localization.md`](Android/workflow/rules/localization.md) | Android localization |
| [`Android/workflow/rules/multiplatform.md`](Android/workflow/rules/multiplatform.md) | Multiplatform |
| [`Android/workflow/rules/ui-design-system.md`](Android/workflow/rules/ui-design-system.md) | Android design system |
| [`Android/workflow/rules/ui-testing.md`](Android/workflow/rules/ui-testing.md) | Android UI testing |
| [`Android/workflow/rules/unit-testing.md`](Android/workflow/rules/unit-testing.md) | Android unit testing |

### Common hooks

| Path | Purpose |
|---|---|
| [`workflow/hooks/hook-runner.py`](workflow/hooks/hook-runner.py) | Portable hook policy runner. Runtime adapters only forward JSON to this SSOT. |

### Common phases

| Path | Purpose |
|---|---|
| [`workflow/phases/archive.md`](workflow/phases/archive.md) | Phase: Archive |
| [`workflow/phases/brainstorming.md`](workflow/phases/brainstorming.md) | Phase: Brainstorming |
| [`workflow/phases/deep-code-review.md`](workflow/phases/deep-code-review.md) | Phase: Deep Code Review |
| [`workflow/phases/discovery.md`](workflow/phases/discovery.md) | Phase: Discovery |
| [`workflow/phases/elaborate.md`](workflow/phases/elaborate.md) | Phase: Elaborate |
| [`workflow/phases/harness-change.md`](workflow/phases/harness-change.md) | Phase: Harness Change |
| [`workflow/phases/harness-review.md`](workflow/phases/harness-review.md) | Phase: Harness Review |
| [`workflow/phases/implement.md`](workflow/phases/implement.md) | Phase: Implement |
| [`workflow/phases/plan.md`](workflow/phases/plan.md) | Phase: Plan |
| [`workflow/phases/pre-commit-check.md`](workflow/phases/pre-commit-check.md) | Phase: Pre-commit Check |
| [`workflow/phases/propose.md`](workflow/phases/propose.md) | Phase: Propose |
| [`workflow/phases/reconcile-implementation.md`](workflow/phases/reconcile-implementation.md) | Phase: Reconcile Implementation |
| [`workflow/phases/verify.md`](workflow/phases/verify.md) | Phase: Verify |
| [`workflow/phases/writing-skills.md`](workflow/phases/writing-skills.md) | Phase: Writing Skills |

### Common roles

| Path | Purpose |
|---|---|
| [`workflow/roles/architecture-designer.md`](workflow/roles/architecture-designer.md) | Role: Architecture Designer |
| [`workflow/roles/bug-investigator.md`](workflow/roles/bug-investigator.md) | Role: Bug Investigator |
| [`workflow/roles/deep-code-reviewer.md`](workflow/roles/deep-code-reviewer.md) | Role: Deep Code Reviewer |
| [`workflow/roles/harness-auditor.md`](workflow/roles/harness-auditor.md) | Role: Harness Auditor |
| [`workflow/roles/implementation-discovery.md`](workflow/roles/implementation-discovery.md) | Role: Implementation Discovery |
| [`workflow/roles/implementation-planner.md`](workflow/roles/implementation-planner.md) | Role: Implementation Planner |
| [`workflow/roles/implementation-writer.md`](workflow/roles/implementation-writer.md) | Role: Implementation Writer |
| [`workflow/roles/product-spec-reviewer.md`](workflow/roles/product-spec-reviewer.md) | Role: Product Spec Reviewer |
| [`workflow/roles/repo-navigator.md`](workflow/roles/repo-navigator.md) | Role: Repo Navigator |
| [`workflow/roles/security-reviewer.md`](workflow/roles/security-reviewer.md) | Role: Security Reviewer |
| [`workflow/roles/specification-writer.md`](workflow/roles/specification-writer.md) | Role: Specification Writer |
| [`workflow/roles/verifier.md`](workflow/roles/verifier.md) | Role: Verifier |

### Common rules

| Path | Purpose |
|---|---|
| [`workflow/rules/agent-roster.md`](workflow/rules/agent-roster.md) | Agent roster |
| [`workflow/rules/archive-lifecycle.md`](workflow/rules/archive-lifecycle.md) | Archive lifecycle |
| [`workflow/rules/artifact-language.md`](workflow/rules/artifact-language.md) | Язык lifecycle-артефактов |
| [`workflow/rules/branching.md`](workflow/rules/branching.md) | Branching and integration |
| [`workflow/rules/bug-investigation.md`](workflow/rules/bug-investigation.md) | Bug investigation |
| [`workflow/rules/code-comments.md`](workflow/rules/code-comments.md) | Code comments |
| [`workflow/rules/code-review.md`](workflow/rules/code-review.md) | Code review |
| [`workflow/rules/coding-standards.md`](workflow/rules/coding-standards.md) | Coding standards |
| [`workflow/rules/developer-experience.md`](workflow/rules/developer-experience.md) | Developer experience |
| [`workflow/rules/git-conventions.md`](workflow/rules/git-conventions.md) | Git conventions |
| [`workflow/rules/hook-contract.md`](workflow/rules/hook-contract.md) | Hook contract |
| [`workflow/rules/implementation-reconciliation.md`](workflow/rules/implementation-reconciliation.md) | Implementation reconciliation |
| [`workflow/rules/memory-architecture.md`](workflow/rules/memory-architecture.md) | Memory architecture |
| [`workflow/rules/orchestration-core.md`](workflow/rules/orchestration-core.md) | Orchestration core |
| [`workflow/rules/platform-change-lifecycle.md`](workflow/rules/platform-change-lifecycle.md) | Platform change lifecycle |
| [`workflow/rules/platform-scope.md`](workflow/rules/platform-scope.md) | Platform scope |
| [`workflow/rules/pre-commit-integrity.md`](workflow/rules/pre-commit-integrity.md) | Pre-commit integrity |
| [`workflow/rules/product-spec-review.md`](workflow/rules/product-spec-review.md) | Independent product specification review |
| [`workflow/rules/repository-documentation.md`](workflow/rules/repository-documentation.md) | Repository documentation |
| [`workflow/rules/runtime-adapters.md`](workflow/rules/runtime-adapters.md) | Runtime adapters |
| [`workflow/rules/security-review.md`](workflow/rules/security-review.md) | Security review |
| [`workflow/rules/specification-layers.md`](workflow/rules/specification-layers.md) | Specification layers |
| [`workflow/rules/system-design.md`](workflow/rules/system-design.md) | Mobile system design |
| [`workflow/rules/system-design/design-gates.md`](workflow/rules/system-design/design-gates.md) | Design gates |
| [`workflow/rules/system-design/estimation-rfc.md`](workflow/rules/system-design/estimation-rfc.md) | Work items and estimation |
| [`workflow/rules/system-design/hdd-ui-principles.md`](workflow/rules/system-design/hdd-ui-principles.md) | Holistic-driven design |
| [`workflow/rules/system-design/landscape.md`](workflow/rules/system-design/landscape.md) | Landscape |
| [`workflow/rules/system-design/mobile-challenges.md`](workflow/rules/system-design/mobile-challenges.md) | Mobile challenges |
| [`workflow/rules/system-design/modularity.md`](workflow/rules/system-design/modularity.md) | Cross-platform modularity |
| [`workflow/rules/system-design/review.md`](workflow/rules/system-design/review.md) | System design review |
| [`workflow/rules/tdd-first.md`](workflow/rules/tdd-first.md) | Behavior-first и TDD |
| [`workflow/rules/test-execution.md`](workflow/rules/test-execution.md) | Test execution |
| [`workflow/rules/verification-evidence.md`](workflow/rules/verification-evidence.md) | Verification evidence |
| [`workflow/rules/verification-matrix.md`](workflow/rules/verification-matrix.md) | Verification method matrix |
| [`workflow/rules/visual-language.md`](workflow/rules/visual-language.md) | Shared visual language |
| [`workflow/rules/wording-clarity.md`](workflow/rules/wording-clarity.md) | Wording clarity |

### Git hooks

| Path | Purpose |
|---|---|
| [`.githooks/pre-commit`](.githooks/pre-commit) | Runtime или Git hook binding |

### Notices

| Path | Purpose |
|---|---|
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | Third-party notices |
| [`third_party/NOTICE.md`](third_party/NOTICE.md) | Third-party provenance |

### Portable skills

| Path | Purpose |
|---|---|
| [`.agents/skills/archive/SKILL.md`](.agents/skills/archive/SKILL.md) | Archive |
| [`.agents/skills/archive/agents/openai.yaml`](.agents/skills/archive/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/brainstorming/SKILL.md`](.agents/skills/brainstorming/SKILL.md) | Brainstorming |
| [`.agents/skills/brainstorming/agents/openai.yaml`](.agents/skills/brainstorming/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/deep-code-review/SKILL.md`](.agents/skills/deep-code-review/SKILL.md) | Deep Code Review |
| [`.agents/skills/deep-code-review/agents/openai.yaml`](.agents/skills/deep-code-review/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/discovery/SKILL.md`](.agents/skills/discovery/SKILL.md) | Discovery |
| [`.agents/skills/discovery/agents/openai.yaml`](.agents/skills/discovery/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/elaborate/SKILL.md`](.agents/skills/elaborate/SKILL.md) | Elaborate |
| [`.agents/skills/elaborate/agents/openai.yaml`](.agents/skills/elaborate/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/harness-change/SKILL.md`](.agents/skills/harness-change/SKILL.md) | Harness Change |
| [`.agents/skills/harness-change/agents/openai.yaml`](.agents/skills/harness-change/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/harness-review/SKILL.md`](.agents/skills/harness-review/SKILL.md) | Harness Review |
| [`.agents/skills/harness-review/agents/openai.yaml`](.agents/skills/harness-review/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/implement/SKILL.md`](.agents/skills/implement/SKILL.md) | Implement |
| [`.agents/skills/implement/agents/openai.yaml`](.agents/skills/implement/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/plan/SKILL.md`](.agents/skills/plan/SKILL.md) | Plan |
| [`.agents/skills/plan/agents/openai.yaml`](.agents/skills/plan/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/pre-commit-check/SKILL.md`](.agents/skills/pre-commit-check/SKILL.md) | Pre-commit Check |
| [`.agents/skills/pre-commit-check/agents/openai.yaml`](.agents/skills/pre-commit-check/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/propose/SKILL.md`](.agents/skills/propose/SKILL.md) | Propose |
| [`.agents/skills/propose/agents/openai.yaml`](.agents/skills/propose/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/reconcile-implementation/SKILL.md`](.agents/skills/reconcile-implementation/SKILL.md) | Reconcile Implementation |
| [`.agents/skills/reconcile-implementation/agents/openai.yaml`](.agents/skills/reconcile-implementation/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/verify/SKILL.md`](.agents/skills/verify/SKILL.md) | Verify |
| [`.agents/skills/verify/agents/openai.yaml`](.agents/skills/verify/agents/openai.yaml) | Codex metadata portable skill |
| [`.agents/skills/writing-skills/SKILL.md`](.agents/skills/writing-skills/SKILL.md) | Writing Skills |
| [`.agents/skills/writing-skills/agents/openai.yaml`](.agents/skills/writing-skills/agents/openai.yaml) | Codex metadata portable skill |

### Process map

| Path | Purpose |
|---|---|
| [`process/README.md`](process/README.md) | Process map |
| [`process/directions/_common.md`](process/directions/_common.md) | Common harness layer |
| [`process/directions/android.md`](process/directions/android.md) | Android direction |
| [`process/directions/ios.md`](process/directions/ios.md) | iOS direction |
| [`process/entities.md`](process/entities.md) | Harness entities |
| [`process/flows.md`](process/flows.md) | Harness flows |

### Root entrypoints

| Path | Purpose |
|---|---|
| [`.gitignore`](.gitignore) | Исключения transient/build state |
| [`AGENTS.md`](AGENTS.md) | AGENTS.md — вход в репозиторий мобильных клиентов |
| [`Android/AGENTS.md`](Android/AGENTS.md) | Android scope |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code adapter |
| [`README.md`](README.md) | Mobile clients |
| [`deep-info.md`](deep-info.md) | Полная карта харнеса |
| [`iOS/AGENTS.md`](iOS/AGENTS.md) | iOS scope |
| [`opencode.json`](opencode.json) | Runtime/configuration contract |
| [`workflow.md`](workflow.md) | Как работать с репозиторием |
| [`workflow/README.md`](workflow/README.md) | Workflow |
| [`workflow/compatibility/modularity-v0.json`](workflow/compatibility/modularity-v0.json) | Runtime/configuration contract |

### Runtime adapters

| Path | Purpose |
|---|---|
| [`.claude/agents/android-build-diagnostician.md`](.claude/agents/android-build-diagnostician.md) | Runtime binding канонической роли |
| [`.claude/agents/android-kotlin-reviewer.md`](.claude/agents/android-kotlin-reviewer.md) | Runtime binding канонической роли |
| [`.claude/agents/android-package-boundary-guard.md`](.claude/agents/android-package-boundary-guard.md) | Runtime binding канонической роли |
| [`.claude/agents/android-ux-designer.md`](.claude/agents/android-ux-designer.md) | Runtime binding канонической роли |
| [`.claude/agents/architecture-designer.md`](.claude/agents/architecture-designer.md) | Runtime binding канонической роли |
| [`.claude/agents/bug-investigator.md`](.claude/agents/bug-investigator.md) | Runtime binding канонической роли |
| [`.claude/agents/deep-code-reviewer.md`](.claude/agents/deep-code-reviewer.md) | Runtime binding канонической роли |
| [`.claude/agents/harness-auditor.md`](.claude/agents/harness-auditor.md) | Runtime binding канонической роли |
| [`.claude/agents/implementation-discovery.md`](.claude/agents/implementation-discovery.md) | Runtime binding канонической роли |
| [`.claude/agents/implementation-planner.md`](.claude/agents/implementation-planner.md) | Runtime binding канонической роли |
| [`.claude/agents/implementation-writer.md`](.claude/agents/implementation-writer.md) | Runtime binding канонической роли |
| [`.claude/agents/ios-package-boundary-guard.md`](.claude/agents/ios-package-boundary-guard.md) | Runtime binding канонической роли |
| [`.claude/agents/ios-ux-designer.md`](.claude/agents/ios-ux-designer.md) | Runtime binding канонической роли |
| [`.claude/agents/product-spec-reviewer.md`](.claude/agents/product-spec-reviewer.md) | Runtime binding канонической роли |
| [`.claude/agents/repo-navigator.md`](.claude/agents/repo-navigator.md) | Runtime binding канонической роли |
| [`.claude/agents/security-reviewer.md`](.claude/agents/security-reviewer.md) | Runtime binding канонической роли |
| [`.claude/agents/specification-writer.md`](.claude/agents/specification-writer.md) | Runtime binding канонической роли |
| [`.claude/agents/verifier.md`](.claude/agents/verifier.md) | Runtime binding канонической роли |
| [`.claude/commands/archive.md`](.claude/commands/archive.md) | Thin runtime command к portable skill |
| [`.claude/commands/brainstorming.md`](.claude/commands/brainstorming.md) | Thin runtime command к portable skill |
| [`.claude/commands/deep-code-review.md`](.claude/commands/deep-code-review.md) | Thin runtime command к portable skill |
| [`.claude/commands/discovery.md`](.claude/commands/discovery.md) | Thin runtime command к portable skill |
| [`.claude/commands/elaborate.md`](.claude/commands/elaborate.md) | Thin runtime command к portable skill |
| [`.claude/commands/harness-change.md`](.claude/commands/harness-change.md) | Thin runtime command к portable skill |
| [`.claude/commands/harness-review.md`](.claude/commands/harness-review.md) | Thin runtime command к portable skill |
| [`.claude/commands/implement.md`](.claude/commands/implement.md) | Thin runtime command к portable skill |
| [`.claude/commands/plan.md`](.claude/commands/plan.md) | Thin runtime command к portable skill |
| [`.claude/commands/pre-commit-check.md`](.claude/commands/pre-commit-check.md) | Thin runtime command к portable skill |
| [`.claude/commands/propose.md`](.claude/commands/propose.md) | Thin runtime command к portable skill |
| [`.claude/commands/reconcile-implementation.md`](.claude/commands/reconcile-implementation.md) | Thin runtime command к portable skill |
| [`.claude/commands/verify.md`](.claude/commands/verify.md) | Thin runtime command к portable skill |
| [`.claude/commands/writing-skills.md`](.claude/commands/writing-skills.md) | Thin runtime command к portable skill |
| [`.claude/settings.json`](.claude/settings.json) | Runtime/configuration contract |
| [`.codex/agents/android-build-diagnostician.toml`](.codex/agents/android-build-diagnostician.toml) | Runtime binding канонической роли |
| [`.codex/agents/android-kotlin-reviewer.toml`](.codex/agents/android-kotlin-reviewer.toml) | Runtime binding канонической роли |
| [`.codex/agents/android-package-boundary-guard.toml`](.codex/agents/android-package-boundary-guard.toml) | Runtime binding канонической роли |
| [`.codex/agents/android-ux-designer.toml`](.codex/agents/android-ux-designer.toml) | Runtime binding канонической роли |
| [`.codex/agents/architecture-designer.toml`](.codex/agents/architecture-designer.toml) | Runtime binding канонической роли |
| [`.codex/agents/bug-investigator.toml`](.codex/agents/bug-investigator.toml) | Runtime binding канонической роли |
| [`.codex/agents/deep-code-reviewer.toml`](.codex/agents/deep-code-reviewer.toml) | Runtime binding канонической роли |
| [`.codex/agents/harness-auditor.toml`](.codex/agents/harness-auditor.toml) | Runtime binding канонической роли |
| [`.codex/agents/implementation-discovery.toml`](.codex/agents/implementation-discovery.toml) | Runtime binding канонической роли |
| [`.codex/agents/implementation-planner.toml`](.codex/agents/implementation-planner.toml) | Runtime binding канонической роли |
| [`.codex/agents/implementation-writer.toml`](.codex/agents/implementation-writer.toml) | Runtime binding канонической роли |
| [`.codex/agents/ios-package-boundary-guard.toml`](.codex/agents/ios-package-boundary-guard.toml) | Runtime binding канонической роли |
| [`.codex/agents/ios-ux-designer.toml`](.codex/agents/ios-ux-designer.toml) | Runtime binding канонической роли |
| [`.codex/agents/product-spec-reviewer.toml`](.codex/agents/product-spec-reviewer.toml) | Runtime binding канонической роли |
| [`.codex/agents/repo-navigator.toml`](.codex/agents/repo-navigator.toml) | Runtime binding канонической роли |
| [`.codex/agents/security-reviewer.toml`](.codex/agents/security-reviewer.toml) | Runtime binding канонической роли |
| [`.codex/agents/specification-writer.toml`](.codex/agents/specification-writer.toml) | Runtime binding канонической роли |
| [`.codex/agents/verifier.toml`](.codex/agents/verifier.toml) | Runtime binding канонической роли |
| [`.codex/hooks.json`](.codex/hooks.json) | Runtime или Git hook binding |
| [`.cursor/agents/android-build-diagnostician.md`](.cursor/agents/android-build-diagnostician.md) | Runtime binding канонической роли |
| [`.cursor/agents/android-kotlin-reviewer.md`](.cursor/agents/android-kotlin-reviewer.md) | Runtime binding канонической роли |
| [`.cursor/agents/android-package-boundary-guard.md`](.cursor/agents/android-package-boundary-guard.md) | Runtime binding канонической роли |
| [`.cursor/agents/android-ux-designer.md`](.cursor/agents/android-ux-designer.md) | Runtime binding канонической роли |
| [`.cursor/agents/architecture-designer.md`](.cursor/agents/architecture-designer.md) | Runtime binding канонической роли |
| [`.cursor/agents/bug-investigator.md`](.cursor/agents/bug-investigator.md) | Runtime binding канонической роли |
| [`.cursor/agents/deep-code-reviewer.md`](.cursor/agents/deep-code-reviewer.md) | Runtime binding канонической роли |
| [`.cursor/agents/harness-auditor.md`](.cursor/agents/harness-auditor.md) | Runtime binding канонической роли |
| [`.cursor/agents/implementation-discovery.md`](.cursor/agents/implementation-discovery.md) | Runtime binding канонической роли |
| [`.cursor/agents/implementation-planner.md`](.cursor/agents/implementation-planner.md) | Runtime binding канонической роли |
| [`.cursor/agents/implementation-writer.md`](.cursor/agents/implementation-writer.md) | Runtime binding канонической роли |
| [`.cursor/agents/ios-package-boundary-guard.md`](.cursor/agents/ios-package-boundary-guard.md) | Runtime binding канонической роли |
| [`.cursor/agents/ios-ux-designer.md`](.cursor/agents/ios-ux-designer.md) | Runtime binding канонической роли |
| [`.cursor/agents/product-spec-reviewer.md`](.cursor/agents/product-spec-reviewer.md) | Runtime binding канонической роли |
| [`.cursor/agents/repo-navigator.md`](.cursor/agents/repo-navigator.md) | Runtime binding канонической роли |
| [`.cursor/agents/security-reviewer.md`](.cursor/agents/security-reviewer.md) | Runtime binding канонической роли |
| [`.cursor/agents/specification-writer.md`](.cursor/agents/specification-writer.md) | Runtime binding канонической роли |
| [`.cursor/agents/verifier.md`](.cursor/agents/verifier.md) | Runtime binding канонической роли |
| [`.cursor/hooks.json`](.cursor/hooks.json) | Runtime или Git hook binding |
| [`.opencode/agents/android-build-diagnostician.md`](.opencode/agents/android-build-diagnostician.md) | Runtime binding канонической роли |
| [`.opencode/agents/android-kotlin-reviewer.md`](.opencode/agents/android-kotlin-reviewer.md) | Runtime binding канонической роли |
| [`.opencode/agents/android-package-boundary-guard.md`](.opencode/agents/android-package-boundary-guard.md) | Runtime binding канонической роли |
| [`.opencode/agents/android-ux-designer.md`](.opencode/agents/android-ux-designer.md) | Runtime binding канонической роли |
| [`.opencode/agents/architecture-designer.md`](.opencode/agents/architecture-designer.md) | Runtime binding канонической роли |
| [`.opencode/agents/bug-investigator.md`](.opencode/agents/bug-investigator.md) | Runtime binding канонической роли |
| [`.opencode/agents/deep-code-reviewer.md`](.opencode/agents/deep-code-reviewer.md) | Runtime binding канонической роли |
| [`.opencode/agents/harness-auditor.md`](.opencode/agents/harness-auditor.md) | Runtime binding канонической роли |
| [`.opencode/agents/implementation-discovery.md`](.opencode/agents/implementation-discovery.md) | Runtime binding канонической роли |
| [`.opencode/agents/implementation-planner.md`](.opencode/agents/implementation-planner.md) | Runtime binding канонической роли |
| [`.opencode/agents/implementation-writer.md`](.opencode/agents/implementation-writer.md) | Runtime binding канонической роли |
| [`.opencode/agents/ios-package-boundary-guard.md`](.opencode/agents/ios-package-boundary-guard.md) | Runtime binding канонической роли |
| [`.opencode/agents/ios-ux-designer.md`](.opencode/agents/ios-ux-designer.md) | Runtime binding канонической роли |
| [`.opencode/agents/product-spec-reviewer.md`](.opencode/agents/product-spec-reviewer.md) | Runtime binding канонической роли |
| [`.opencode/agents/repo-navigator.md`](.opencode/agents/repo-navigator.md) | Runtime binding канонической роли |
| [`.opencode/agents/security-reviewer.md`](.opencode/agents/security-reviewer.md) | Runtime binding канонической роли |
| [`.opencode/agents/specification-writer.md`](.opencode/agents/specification-writer.md) | Runtime binding канонической роли |
| [`.opencode/agents/verifier.md`](.opencode/agents/verifier.md) | Runtime binding канонической роли |
| [`.opencode/commands/archive.md`](.opencode/commands/archive.md) | Thin runtime command к portable skill |
| [`.opencode/commands/brainstorming.md`](.opencode/commands/brainstorming.md) | Thin runtime command к portable skill |
| [`.opencode/commands/deep-code-review.md`](.opencode/commands/deep-code-review.md) | Thin runtime command к portable skill |
| [`.opencode/commands/discovery.md`](.opencode/commands/discovery.md) | Thin runtime command к portable skill |
| [`.opencode/commands/elaborate.md`](.opencode/commands/elaborate.md) | Thin runtime command к portable skill |
| [`.opencode/commands/harness-change.md`](.opencode/commands/harness-change.md) | Thin runtime command к portable skill |
| [`.opencode/commands/harness-review.md`](.opencode/commands/harness-review.md) | Thin runtime command к portable skill |
| [`.opencode/commands/implement.md`](.opencode/commands/implement.md) | Thin runtime command к portable skill |
| [`.opencode/commands/plan.md`](.opencode/commands/plan.md) | Thin runtime command к portable skill |
| [`.opencode/commands/pre-commit-check.md`](.opencode/commands/pre-commit-check.md) | Thin runtime command к portable skill |
| [`.opencode/commands/propose.md`](.opencode/commands/propose.md) | Thin runtime command к portable skill |
| [`.opencode/commands/reconcile-implementation.md`](.opencode/commands/reconcile-implementation.md) | Thin runtime command к portable skill |
| [`.opencode/commands/verify.md`](.opencode/commands/verify.md) | Thin runtime command к portable skill |
| [`.opencode/commands/writing-skills.md`](.opencode/commands/writing-skills.md) | Thin runtime command к portable skill |
| [`.opencode/plugins/harness-hooks.ts`](.opencode/plugins/harness-hooks.ts) | Runtime или Git hook binding |

### Scripts

| Path | Purpose |
|---|---|
| [`workflow/scripts/archive-change.py`](workflow/scripts/archive-change.py) | Collision-safe dry-run/apply archive for implementation and product packages. |
| [`workflow/scripts/artifact_language.py`](workflow/scripts/artifact_language.py) | Shared Russian authored-prose validation for lifecycle artifacts. |
| [`workflow/scripts/capture-verification-state.py`](workflow/scripts/capture-verification-state.py) | Capture or inspect a deterministic verification state fingerprint. |
| [`workflow/scripts/configure-git-hooks.sh`](workflow/scripts/configure-git-hooks.sh) | Runtime или Git hook binding |
| [`workflow/scripts/deep-code-review-readonly-guard.py`](workflow/scripts/deep-code-review-readonly-guard.py) | Machine-enforced pre/post mutation guard for read-only deep-code-review. |
| [`workflow/scripts/deep_code_review_report.py`](workflow/scripts/deep_code_review_report.py) | Bounded no-follow report snapshot primitive shared by validator and reader. |
| [`workflow/scripts/find-platform-context.py`](workflow/scripts/find-platform-context.py) | Build a small adapter-backed context packet for a platform feature. |
| [`workflow/scripts/git_change_paths.py`](workflow/scripts/git_change_paths.py) | Canonical Git change entries and identity/mutable/read-only path sets. |
| [`workflow/scripts/harness-docs.py`](workflow/scripts/harness-docs.py) | Render and verify deterministic root documentation projections. |
| [`workflow/scripts/harness-lint.py`](workflow/scripts/harness-lint.py) | Deterministic structural checks for the repository workflow harness. |
| [`workflow/scripts/harness-security-audit.py`](workflow/scripts/harness-security-audit.py) | Bounded, deterministic and non-mutating security scan of harness surfaces. |
| [`workflow/scripts/platform_path_ownership.py`](workflow/scripts/platform_path_ownership.py) | Canonical fail-closed platform writable-path ownership checks. |
| [`workflow/scripts/platform_rule_profiles.py`](workflow/scripts/platform_rule_profiles.py) | Canonical validation and resolution for platform engineering rule profiles. |
| [`workflow/scripts/pre-commit-check.py`](workflow/scripts/pre-commit-check.py) | Staged-index pre-commit gate. Never stages, commits, pushes, or prints secrets. |
| [`workflow/scripts/read-deep-code-review-report.py`](workflow/scripts/read-deep-code-review-report.py) | Read a validated feedback report only when its bounded snapshot still matches. |
| [`workflow/scripts/reconcile-implementation.py`](workflow/scripts/reconcile-implementation.py) | Inspect and guard explicit pre-delivery implementation reconciliation. |
| [`workflow/scripts/test-watchdog.sh`](workflow/scripts/test-watchdog.sh) | Исполняемый adapter харнеса |
| [`workflow/scripts/validate-deep-code-review.py`](workflow/scripts/validate-deep-code-review.py) | Fail-closed, read-only validator for the deep-code-review public contract. |
| [`workflow/scripts/validate-implementation-scope.py`](workflow/scripts/validate-implementation-scope.py) | Baseline/check guard for one implementation task's mutable scope. |
| [`workflow/scripts/validate-platform-change.py`](workflow/scripts/validate-platform-change.py) | Fail-closed validator for adapter-backed platform change packages. |
| [`workflow/scripts/validate-product-spec.py`](workflow/scripts/validate-product-spec.py) | Fingerprint and validate shared product review provenance attestations. |
| [`workflow/scripts/workflow-reflection.py`](workflow/scripts/workflow-reflection.py) | Print a focused reflection checklist without repository-specific dependencies. |

### Spec schema indexes

| Path | Purpose |
|---|---|
| [`Android/specs/README.md`](Android/specs/README.md) | Android implementation specifications |
| [`iOS/specs/README.md`](iOS/specs/README.md) | iOS implementation specifications |
| [`specs/product/README.md`](specs/product/README.md) | Shared product specifications |

### Templates

| Path | Purpose |
|---|---|
| [`workflow/templates/harness-change.md`](workflow/templates/harness-change.md) | Harness Change Plan — <short-name> |
| [`workflow/templates/native-verification-observation.json`](workflow/templates/native-verification-observation.json) | Runtime/configuration contract |
| [`workflow/templates/platform-design.md`](workflow/templates/platform-design.md) | Design — <feature> / <platform> / <change-id> |
| [`workflow/templates/platform-implementation-spec.md`](workflow/templates/platform-implementation-spec.md) | Implementation spec — <feature> / <platform> / <change-id> |
| [`workflow/templates/platform-meta.json`](workflow/templates/platform-meta.json) | Runtime/configuration contract |
| [`workflow/templates/platform-plan-readme.md`](workflow/templates/platform-plan-readme.md) | Plan — <feature> / <platform> / <change-id> |
| [`workflow/templates/platform-plan-task.md`](workflow/templates/platform-plan-task.md) | task-NNN — <название> |
| [`workflow/templates/platform-proposal.md`](workflow/templates/platform-proposal.md) | Proposal — <feature> / <platform> / <change-id> |
| [`workflow/templates/platform-rule-selection.json`](workflow/templates/platform-rule-selection.json) | Runtime/configuration contract |
| [`workflow/templates/platform-task-evidence.md`](workflow/templates/platform-task-evidence.md) | Task Evidence — task-NNN |
| [`workflow/templates/platform-ux.md`](workflow/templates/platform-ux.md) | <Feature> — <Platform> native UX |
| [`workflow/templates/platform-verification.md`](workflow/templates/platform-verification.md) | Verification — <feature> / <platform> / <change-id> |
| [`workflow/templates/product-archive-request.json`](workflow/templates/product-archive-request.json) | Runtime/configuration contract |
| [`workflow/templates/product-brief.md`](workflow/templates/product-brief.md) | <Feature> — product brief |
| [`workflow/templates/product-concept.md`](workflow/templates/product-concept.md) | <Feature> — concept |
| [`workflow/templates/product-review-verdict.json`](workflow/templates/product-review-verdict.json) | Runtime/configuration contract |
| [`workflow/templates/product-spec.md`](workflow/templates/product-spec.md) | <Feature> — shared product specification |
| [`workflow/templates/product-ux.md`](workflow/templates/product-ux.md) | <Feature> — shared product UX |

### Test evidence

| Path | Purpose |
|---|---|
| [`workflow/test-evidence/README.md`](workflow/test-evidence/README.md) | Test evidence |
| [`workflow/test-evidence/android-propose-plan-implement.md`](workflow/test-evidence/android-propose-plan-implement.md) | Android propose/plan/implement — RED/GREEN |
| [`workflow/test-evidence/android-verify-archive.md`](workflow/test-evidence/android-verify-archive.md) | Android Verify и implementation archive |
| [`workflow/test-evidence/archive-receipt-cli.md`](workflow/test-evidence/archive-receipt-cli.md) | Archive receipt CLI evidence |
| [`workflow/test-evidence/concurrent-work-lanes.md`](workflow/test-evidence/concurrent-work-lanes.md) | Concurrent work lanes — test evidence |
| [`workflow/test-evidence/cross-platform-modularity.md`](workflow/test-evidence/cross-platform-modularity.md) | Cross-platform modularity — RED → GREEN → REFACTOR |
| [`workflow/test-evidence/deep-code-review.md`](workflow/test-evidence/deep-code-review.md) | Deep code review evidence |
| [`workflow/test-evidence/durable-feature-specifications.md`](workflow/test-evidence/durable-feature-specifications.md) | Durable feature specifications — RED → GREEN → REFACTOR |
| [`workflow/test-evidence/harness-bootstrap.md`](workflow/test-evidence/harness-bootstrap.md) | Harness bootstrap — test evidence |
| [`workflow/test-evidence/implementation-reconciliation.md`](workflow/test-evidence/implementation-reconciliation.md) | Implementation reconciliation evidence |
| [`workflow/test-evidence/implementation-retirement.md`](workflow/test-evidence/implementation-retirement.md) | Implementation retirement evidence |
| [`workflow/test-evidence/independent-product-review.md`](workflow/test-evidence/independent-product-review.md) | Independent product specification review evidence |
| [`workflow/test-evidence/ios-engineering-rules.md`](workflow/test-evidence/ios-engineering-rules.md) | iOS engineering rules — RED/GREEN evidence |
| [`workflow/test-evidence/ios-implement-archive.md`](workflow/test-evidence/ios-implement-archive.md) | iOS implement/verify/archive — test evidence |
| [`workflow/test-evidence/ios-propose-plan.md`](workflow/test-evidence/ios-propose-plan.md) | iOS propose/plan — test evidence |
| [`workflow/test-evidence/ios-ui-runner-recovery.md`](workflow/test-evidence/ios-ui-runner-recovery.md) | iOS UI runner recovery — harness change evidence |
| [`workflow/test-evidence/lifecycle-flow-hardening.md`](workflow/test-evidence/lifecycle-flow-hardening.md) | Lifecycle flow hardening — test evidence |
| [`workflow/test-evidence/plan-task-deliverables.md`](workflow/test-evidence/plan-task-deliverables.md) | Plan task deliverables — RED/GREEN |
| [`workflow/test-evidence/platform-native-ux.md`](workflow/test-evidence/platform-native-ux.md) | Platform-native UX harness evidence |
| [`workflow/test-evidence/post-archive-commit-gate.md`](workflow/test-evidence/post-archive-commit-gate.md) | Post-archive commit gate evidence |
| [`workflow/test-evidence/pre-commit-and-hooks.md`](workflow/test-evidence/pre-commit-and-hooks.md) | Pre-commit and hooks evidence |
| [`workflow/test-evidence/product-elaboration.md`](workflow/test-evidence/product-elaboration.md) | Product elaboration skills — test evidence |
| [`workflow/test-evidence/relaxed-post-archive-delivery-gate.md`](workflow/test-evidence/relaxed-post-archive-delivery-gate.md) | Relaxed post-archive delivery gate |
| [`workflow/test-evidence/root-documentation.md`](workflow/test-evidence/root-documentation.md) | Root project documentation |
| [`workflow/test-evidence/russian-platform-artifacts.md`](workflow/test-evidence/russian-platform-artifacts.md) | Russian platform artifacts — RED → GREEN → REFACTOR |
| [`workflow/test-evidence/simple-model-task-evidence.md`](workflow/test-evidence/simple-model-task-evidence.md) | Simple-model task evidence — RED → GREEN → REFACTOR |

### iOS harness

| Path | Purpose |
|---|---|
| [`iOS/workflow/README.md`](iOS/workflow/README.md) | iOS workflow addenda |
| [`iOS/workflow/phases/archive.md`](iOS/workflow/phases/archive.md) | iOS addendum: Archive |
| [`iOS/workflow/phases/deep-code-review.md`](iOS/workflow/phases/deep-code-review.md) | iOS addendum: Deep Code Review |
| [`iOS/workflow/phases/implement.md`](iOS/workflow/phases/implement.md) | iOS addendum: Implement |
| [`iOS/workflow/phases/plan.md`](iOS/workflow/phases/plan.md) | iOS addendum: Plan |
| [`iOS/workflow/phases/pre-commit-check.md`](iOS/workflow/phases/pre-commit-check.md) | iOS addendum: Pre-commit Check |
| [`iOS/workflow/phases/propose.md`](iOS/workflow/phases/propose.md) | iOS addendum: Propose |
| [`iOS/workflow/phases/reconcile-implementation.md`](iOS/workflow/phases/reconcile-implementation.md) | iOS addendum: Reconcile Implementation |
| [`iOS/workflow/phases/verify.md`](iOS/workflow/phases/verify.md) | iOS addendum: Verify |
| [`iOS/workflow/platform-contract.json`](iOS/workflow/platform-contract.json) | Capability, profile и ownership contract платформы |
| [`iOS/workflow/roles/ios-package-boundary-guard.md`](iOS/workflow/roles/ios-package-boundary-guard.md) | Role: iOS Package Boundary Guard |
| [`iOS/workflow/roles/ios-ux-designer.md`](iOS/workflow/roles/ios-ux-designer.md) | Role: iOS UX Designer |
| [`iOS/workflow/rules/accessibility.md`](iOS/workflow/rules/accessibility.md) | iOS accessibility |
| [`iOS/workflow/rules/app-development.md`](iOS/workflow/rules/app-development.md) | iOS application development |
| [`iOS/workflow/rules/architecture.md`](iOS/workflow/rules/architecture.md) | iOS architecture |
| [`iOS/workflow/rules/architecture/dependency-injection.md`](iOS/workflow/rules/architecture/dependency-injection.md) | Dependency injection |
| [`iOS/workflow/rules/architecture/error-handling.md`](iOS/workflow/rules/architecture/error-handling.md) | Error handling |
| [`iOS/workflow/rules/architecture/feature-first.md`](iOS/workflow/rules/architecture/feature-first.md) | Feature-First |
| [`iOS/workflow/rules/architecture/legacy.md`](iOS/workflow/rules/architecture/legacy.md) | Existing and legacy fit |
| [`iOS/workflow/rules/architecture/mvvm.md`](iOS/workflow/rules/architecture/mvvm.md) | MVVM |
| [`iOS/workflow/rules/architecture/naming.md`](iOS/workflow/rules/architecture/naming.md) | Naming |
| [`iOS/workflow/rules/architecture/types-clean-code.md`](iOS/workflow/rules/architecture/types-clean-code.md) | Type design |
| [`iOS/workflow/rules/architecture/use-cases.md`](iOS/workflow/rules/architecture/use-cases.md) | Use Cases |
| [`iOS/workflow/rules/ios-pitfalls.md`](iOS/workflow/rules/ios-pitfalls.md) | Apple SDK design checks |
| [`iOS/workflow/rules/localization.md`](iOS/workflow/rules/localization.md) | iOS localization |
| [`iOS/workflow/rules/package-development.md`](iOS/workflow/rules/package-development.md) | iOS physical modularity |
| [`iOS/workflow/rules/performance.md`](iOS/workflow/rules/performance.md) | iOS performance |
| [`iOS/workflow/rules/performance/app-launch.md`](iOS/workflow/rules/performance/app-launch.md) | App launch performance |
| [`iOS/workflow/rules/performance/concurrency.md`](iOS/workflow/rules/performance/concurrency.md) | Concurrency performance |
| [`iOS/workflow/rules/performance/measure-first.md`](iOS/workflow/rules/performance/measure-first.md) | Measure first |
| [`iOS/workflow/rules/performance/memory.md`](iOS/workflow/rules/performance/memory.md) | Memory performance |
| [`iOS/workflow/rules/performance/networking.md`](iOS/workflow/rules/performance/networking.md) | Networking performance |
| [`iOS/workflow/rules/performance/profiling.md`](iOS/workflow/rules/performance/profiling.md) | Profiling |
| [`iOS/workflow/rules/performance/swiftui-rendering.md`](iOS/workflow/rules/performance/swiftui-rendering.md) | SwiftUI rendering performance |
| [`iOS/workflow/rules/simulator.md`](iOS/workflow/rules/simulator.md) | Simulator execution |
| [`iOS/workflow/rules/swift-concurrency.md`](iOS/workflow/rules/swift-concurrency.md) | Swift concurrency |
| [`iOS/workflow/rules/swift-style.md`](iOS/workflow/rules/swift-style.md) | Swift style |
| [`iOS/workflow/rules/ui-design-system.md`](iOS/workflow/rules/ui-design-system.md) | iOS design-system integration |
| [`iOS/workflow/rules/ui-test-spec.md`](iOS/workflow/rules/ui-test-spec.md) | UI test specification |
| [`iOS/workflow/rules/ui-testing.md`](iOS/workflow/rules/ui-testing.md) | iOS UI testing |
| [`iOS/workflow/rules/unit-testing.md`](iOS/workflow/rules/unit-testing.md) | iOS unit testing |
| [`iOS/workflow/rules/xcode.md`](iOS/workflow/rules/xcode.md) | iOS Xcode integration |
<!-- END GENERATED: DEEP_INVENTORY -->

## Runtime parity

Четыре runtime используют одинаковые portable skills и канонические роли.
Различается только способ discovery/explicit command и hook binding.

<!-- BEGIN GENERATED: DEEP_RUNTIME_PARITY -->
| Runtime | Skill discovery | Skill entry coverage | Role bindings | Hook/config binding |
|---|---|---:|---:|---|
| Codex | [`.agents/skills/`](.agents/skills/) | native 14/14 | 18/18 | [`.codex/hooks.json`](.codex/hooks.json) |
| Claude Code | [`.agents/skills/`](.agents/skills/) | thin 14/14 | 18/18 | [`.claude/settings.json`](.claude/settings.json) |
| Cursor | [`.agents/skills/`](.agents/skills/) | native 14/14 | 18/18 | [`.cursor/hooks.json`](.cursor/hooks.json) |
| OpenCode | [`.agents/skills/`](.agents/skills/) | thin 14/14 | 18/18 | [`.opencode/plugins/harness-hooks.ts`](.opencode/plugins/harness-hooks.ts) |

Portable skills: **14**. Canonical/runtime roles: **18** per runtime.
Claude Code и OpenCode имеют thin command для каждого skill; Codex и Cursor используют native discovery portable SSOT.
<!-- END GENERATED: DEEP_RUNTIME_PARITY -->

## Freshness contract

[`workflow/scripts/harness-docs.py`](workflow/scripts/harness-docs.py) различает:

- structural freshness — exact filenames/markers, inventory, capability/profile
  graph, skill↔phase, role/command parity, JSON/frontmatter и local links;
- semantic freshness — корректность manual prose, audience layering, ownership,
  platform claims и invocation semantics; это проверяет `harness-review` и
  read-only auditor.

`render` меняет только содержимое exact generated markers и сохраняет остальные
байты manual prose. `check` ничего не пишет и fail-closed при stale/missing
surface. Generated block нельзя править вручную: источник меняют в каноне,
затем повторяют render/check.
