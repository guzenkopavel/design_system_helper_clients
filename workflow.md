# Как работать с репозиторием

Это практическое руководство для любого уровня знакомства с проектом. Оно
объясняет выбор маршрута и ожидаемые артефакты, но не заменяет канонические
правила из [`workflow/`](workflow/) и platform addenda.

## С чего начать

```text
Есть новая идея или меняется observable behavior?
  да → brainstorming? → discovery → elaborate → product approval
       → propose для iOS и/или Android
  нет → доказать Product impact assessment: NONE
       → propose --technical-only для нужной платформы

Есть уже approved shared spec или доказанный technical-only intake?
  да → propose → plan → implement → verify → archive implementation
  нет → вернуться к product elaboration

Меняется сам workflow-харнес?
  да → harness-change → harness-review

Есть явный commit intent с platform production changes?
  да → explicit intended paths → reconcile-implementation per platform package
       → report → scoped staging → pre-commit-check → commit
```

`brainstorming` полезен для сырой идеи и альтернатив, но может быть пропущен,
если решение уже достаточно определено. `discovery` и `elaborate` обязательны
для product-backed изменения: первый создаёт brief, второй доводит shared
package до `READY / APPROVED` и останавливается перед platform fan-out.

Внутри `$elaborate` READY теперь проходит независимый цикл:

```text
DRAFT candidate → review/fix cycles → explicit human approval
→ fresh snapshot → coordinator создаёт 6 contexts и сохраняет runtime evidence
→ one-parent verdict attestations → PASS/GAPS/UNKNOWN review-verdicts.json
→ Status READY + Readiness Decision READY/none
→ validate-product-spec.py check → STOP
```

Каждый context видит один lens и один fingerprint, но не writer rationale или
другие verdicts. Validator проверяет schema/provenance attestation/freshness,
но не доказывает isolation: её обеспечивает реальный runtime invocation.
Product и cross-client parity обязательны. Если runtime не может создать fresh
context/evidence, durable результат `UNKNOWN`, package остаётся DRAFT.
Любая последующая package-правка кроме exact Status metadata делает receipt
stale и повторяет все шесть final reviews.
Client Readiness оценивает полноту shared contract отдельно для iOS/Android, а
не состояние implementation. Каждый AC задаёт один observable outcome и одну
уникальную evidence dimension; отдельно наблюдаемые accessibility/appearance
outcomes не объединяются под одним PASS.

## Portable skills

Все runtime читают один skill SSOT из [`.agents/skills/`](.agents/skills/).
Codex вызывает skill как `$<name>`, остальные поддерживаемые runtime — через
`/<name>` или native skill discovery. Generated-матрица показывает текущие 14
skills, их канонические phases и write contract.

<!-- BEGIN GENERATED: WORKFLOW_SKILLS -->
| Skill | Назначение | Каноническая phase | Пишет | Verification |
|---|---|---|---|---|
| `archive` | Collision-safe архивировать verified platform change или явно retired shared product package. Использовать только по явному `$archive implementation ...` либо `$archive product ...`. | [`workflow/phases/archive.md`](workflow/phases/archive.md) | `platform archive package, durable SPECIFICATION.md and ARCHIVED.md tombstone`, `product archive package, durable SPECIFICATION.md and spec.md tombstone` | `terminal` |
| `brainstorming` | Исследовать сырую продуктовую идею до спецификации и кода, когда проблема, scope, trade-offs или направление ещё не ясны; сформировать 2–3 реальных варианта, рекомендацию и open questions для общего iOS/Android product layer. | [`workflow/phases/brainstorming.md`](workflow/phases/brainstorming.md) | `specs/product/<feature>/concept.md (optional)` | `smoke` |
| `deep-code-review` | Выполнить единый read-only deep review, triage feedback, доказательное bug investigation или security audit. Использовать только при явном `$deep-code-review`; fixes и lifecycle mutations запрещены. | [`workflow/phases/deep-code-review.md`](workflow/phases/deep-code-review.md) | нет | `focused` |
| `discovery` | Превратить идею или выбранный concept в общий для iOS и Android product brief с evidence, scope, draft screen/flow impact, secondary concerns и черновыми REQ/AC; использовать для новой или неоднозначной продуктовой функциональности до финальной спеки. | [`workflow/phases/discovery.md`](workflow/phases/discovery.md) | `specs/product/<feature>/brief.md` | `focused` |
| `elaborate` | Вручную провести продуктовую фичу через discovery, shared UX для UI scope, product review lenses и явный human approval до общей READY-спеки для iOS/Android, затем остановиться перед платформенным fan-out. | [`workflow/phases/elaborate.md`](workflow/phases/elaborate.md) | `specs/product/<feature>/brief.md`, `specs/product/<feature>/ux.md (UI/interaction only)`, `specs/product/<feature>/spec.md`, `specs/product/<feature>/review-verdicts.json` | `focused` |
| `harness-change` | Изменять сам workflow-харнес репозитория — правила, фазы, skills, команды, роли, hooks, скрипты, шаблоны и process map. Использовать по явному вызову harness-change или когда нужно добавить, изменить, переместить либо удалить harness-механику с проверкой common/iOS/Android scope, wiring cascade и финальным harness-review. | [`workflow/phases/harness-change.md`](workflow/phases/harness-change.md) | `canonical harness files`, `synchronized runtime adapters and process map`, `workflow/test-evidence/<name>.md for hard changes` | `focused` |
| `harness-review` | Проверять сам workflow-харнес репозитория на структурную и смысловую согласованность. Использовать по явному вызову harness-review, после harness-change или для периодического аудита правил, фаз, skills, ролей, hooks и process map; совмещать детерминированный lint, read-only аудит и отдельные iOS/Android evidence для cross-platform scope. | [`workflow/phases/harness-review.md`](workflow/phases/harness-review.md) | нет | `true` |
| `implement` | Выполнить ready tasks platform package при поддержанной implement capability. | [`workflow/phases/implement.md`](workflow/phases/implement.md) | `task-declared production paths`, `<platform>/specs/<feature>/changes/<change-id>/evidence/task-NNN.md`, `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md` | `focused` |
| `plan` | Создать self-contained platform plan при поддержанной plan capability. | [`workflow/phases/plan.md`](workflow/phases/plan.md) | `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/README.md`, `<platform>/specs/<feature>/changes/<change-id>/plan/rule-selection.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md` | `focused` |
| `pre-commit-check` | Проверить staged index перед явным commit intent. Использовать при `$pre-commit-check` и всегда перед выполнением просьбы commit/закомить; gate сам не stage/commit/push. | [`workflow/phases/pre-commit-check.md`](workflow/phases/pre-commit-check.md) | нет | `staged-index` |
| `propose` | Создать platform implementation package при поддержанной propose capability. | [`workflow/phases/propose.md`](workflow/phases/propose.md) | `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/proposal.md`, `<platform>/specs/<feature>/changes/<change-id>/implementation-spec.md`, `<platform>/specs/<feature>/changes/<change-id>/design.md`, `<platform>/specs/<feature>/changes/<change-id>/verification.md`, `<platform>/specs/<feature>/changes/<change-id>/platform-ux.md (product-backed ui only)` | `focused` |
| `reconcile-implementation` | Сверить явный набор platform production changes с active implementation package до staging и безопасно восстановить package evidence/state. | [`workflow/phases/reconcile-implementation.md`](workflow/phases/reconcile-implementation.md) | `<platform>/specs/<feature>/changes/<change-id>/implementation-spec.md`, `<platform>/specs/<feature>/changes/<change-id>/design.md`, `<platform>/specs/<feature>/changes/<change-id>/verification.md`, `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/`, `<platform>/specs/<feature>/changes/<change-id>/evidence/reconciliation-*.md` | `focused-and-implement-validator` |
| `verify` | Проверить platform package при поддержанной verify capability и получить fresh terminal evidence. | [`workflow/phases/verify.md`](workflow/phases/verify.md) | `<platform>/specs/<feature>/changes/<change-id>/verification.md`, `<platform>/specs/<feature>/changes/<change-id>/evidence/`, `<platform>/specs/<feature>/changes/<change-id>/meta.json`, `<platform>/specs/<feature>/changes/<change-id>/plan/task-NNN.md (recovery only)` | `terminal` |
| `writing-skills` | Проверять новые жёсткие workflow-правила, skills и runtime-роли через RED → GREEN → REFACTOR и сохранять test evidence. Использовать как обязательную зависимость harness-change при добавлении или существенном изменении инструктивного поведения; не использовать для typo, link fix, index и неинструктивной документации. | [`workflow/phases/writing-skills.md`](workflow/phases/writing-skills.md) | `workflow/test-evidence/<name>.md` | `true` |
<!-- END GENERATED: WORKFLOW_SKILLS -->

## Синтаксис вызовов

Ниже `$` означает Codex-вход; в runtime со slash-командами используйте то же
имя после `/`.

```text
$brainstorming <feature-or-idea>
$discovery <feature>
$elaborate <feature>

$propose <platform> <feature> [--change <change-id>] [--tier quick|standard|extended] [--technical-only]
$plan <platform> <feature> [--change <change-id>]
$implement <platform> <feature> [--change <change-id>] [--task <task-id>|--all]
$verify <platform> <feature> [--change <change-id>]
$reconcile-implementation <platform> <feature> [--change <change-id>] --path <repo-relative> [--path ...]
$archive implementation <platform> <feature> [--change <change-id>]
$archive product <feature>

$deep-code-review review <platform> <feature> [--change <change-id>] [--against <git-ref>|--paths <...>]
$deep-code-review feedback <platform> <feature> [--change <change-id>] --report-source <stdin|safe-repo-path>
$deep-code-review bug <platform> <feature> [--change <change-id>] <symptom-or-finding>
$deep-code-review security [--json]
$pre-commit-check
$harness-change <change>
$harness-review <scope>
$writing-skills <instructional-change>
```

`platform` обязателен для platform lifecycle и принимает adapter identity
`ios` или `android`. Если `--change` опущен downstream, активный package должен
быть единственным. Manual-only skills не запускаются из произвольного контекста
и не дают разрешения на commit, push или расширение scope. Явный commit intent
является разрешённым coordinator trigger для reconciliation, но только с
явным intended path set и отдельным вызовом на каждую platform package identity.

## Product-backed и technical-only

Product-backed flow хранит единый контракт в
[`specs/product/<feature>/`](specs/product/): `concept.md`, `brief.md`, при
необходимости `ux.md`, затем `spec.md`. До `READY`, явного human approval,
полного REQ↔AC coverage и закрытых blockers platform fan-out запрещён.
Если feature уже доставлена, `SPECIFICATION.md` в том же root является
read-only current baseline для нового candidate и не входит в его review
fingerprint.

Technical-only flow не создаёт shared spec только при доказанном
`Product impact assessment: NONE`. Evidence должно показывать, что observable
behavior, product requirements и acceptance criteria не меняются. `PRESENT`
или `UNCERTAIN` возвращает работу в `discovery → elaborate`. Каноническая
граница описана в
[`workflow/rules/specification-layers.md`](workflow/rules/specification-layers.md).

## Platform lifecycle: что и когда записывается

Обе платформы используют одинаковые статусы и общие phases, но читают разные
adapter profiles, addenda, source/build topology и evidence. Успешная проверка
iOS не доказывает Android и наоборот.

Для новых v1 packages все четыре lifecycle profile всегда включают common modularity rule и
platform addendum. Propose фиксирует structured `isolated | deviation |
not-applicable` и получает `PASS` boundary guard. Новые cohesive feature/data/
network/storage/reusable UI capabilities по strong default получают physical
platform unit; application shell оставляет только entry/lifecycle/root routing/
DI/config/resources и composition. Plan создаёт wiring/API/consumer/app-shell
tasks с boundary owner. Каждая current v1 task отдельно содержит
`Implementation deliverables`: минимум два пункта о том, что будет реализовано;
`Steps` описывает способ выполнения, а `Expected result` — доказанный итог.
`Paths` содержит только writable production authority,
а lifecycle/spec/rule refs живут в immutable `Read-only context`; mode=plan
проверяет adapter boundaries, classification, duplicates и ancestor overlap.
Verify проверяет realized graph. Folder/layer не
является module; unavailable graph/tooling даёт `UNKNOWN`.

Legacy v0 не определяется по одному отсутствующему version field. Он допустим
только для identities и immutable hashes из
[`workflow/compatibility/modularity-v0.json`](workflow/compatibility/modularity-v0.json).
Такой package завершает только исторические task paths/checks; значения task
Status/Evidence и lifecycle meta/evidence могут продвигаться, но design,
immutable meta, plan/task graph и ownership не расширяются. V1 composition
правило к нему ретроактивно не применяется.
Canonical registry digest и exact two identities pinned в common resolver;
registry-only append/edit, extra meta key или изменение `blocking_questions`
блокируется до отдельного code+registry harness change и audit.

Все четыре v1 lifecycle profile также включают
[`artifact-language.md`](workflow/rules/artifact-language.md). Пояснения,
решения, требования, шаги и verification reports в platform Markdown пишутся
по-русски; code/API names, repo paths, IDs и точная machine schema сохраняются
без перевода. Валидатор проверяет каждый содержательный block независимо, так
что один русский padding paragraph не легализует English sections. То же
правило действует для authored product prose и human-authored JSON
rationale/findings/meta; общий helper блокирует отдельное English sentence даже
рядом с длинным русским padding. Platform authored-meta gate применяется только
к current v1. Исторический
registry-anchored v0 исключён из правила из-за неизменяемых hash anchors.

| Шаг | Вход | Основные записи | Успешный статус |
|---|---|---|---|
| `propose` | approved product spec или technical-only evidence | `proposal.md`, `implementation-spec.md`, `design.md`, `verification.md`, `meta.json` | `specified` |
| `plan` | `specified` package | `plan/README.md`, `plan/task-*.md`, sealed `plan/rule-selection.json` | `planned` |
| `implement` | ready task/DAG | production только в task scope, focused task evidence, task/meta status | `implementing` |
| `verify` | все tasks done | `verification.md`, scoped `evidence/`/meta и fingerprint при PASS; reopening `plan/task-NNN.md` только при non-PASS recovery | `verified` |
| `archive implementation` | fresh verified package | immutable archive, receipt, current `SPECIFICATION.md`, active tombstone | `archived` |

Для product-backed `ui` внутри Propose действует строгая последовательность:
`specification-writer → adapter UX designer → platform-ux.md READY →
architecture-designer`. Plan трассирует UI tasks к artifact/native checks,
Implement и Verify перечитывают его и собирают appearance evidence. iOS owner
проверяет Liquid Glass availability/fallback, Android owner держит Material 3
baseline и не предполагает M3 Expressive/dynamic color.

Package schema живёт в `<platform>/specs/<feature>/changes/<change-id>/`.
`implement` — единственная lifecycle phase, которая пишет native production.
`verify` читает production, пишет `verification.md`, scoped evidence/meta и
ставит точный `PASS`, `FAIL` или `UNKNOWN`. Каждая atomic evidence obligation
имеет отдельную row; unobserved dimension остаётся `UNKNOWN` и не скрывается
соседним PASS. При non-PASS coordinator также
переоткрывает только contract-mapped tasks и их dependent closure в
`plan/task-NNN.md`; production остаётся read-only. Archive coordinator сначала
выполняет canonical script как dry-run и использует его `--apply` только после
отдельного явного apply intent и green gates.
Product retirement request по умолчанию живёт вне active fingerprint в
`specs/product/_retirement-requests/<feature>/<date-feature>.json`; apply
сохраняет validated copy в archive как `retirement-request.json`.
Implementation archive публикует полный verified post-change contract в
platform feature-root `SPECIFICATION.md`. Product `completed` публикует approved
product baseline; `superseded`/`cancelled` сохраняет прежний baseline и не
продвигает retired candidate. Любой archive остаётся immutable history.

Scope baseline использует schema v3 `git-visible-lane-v1`: tracked и
non-ignored untracked файлы selected package/Paths/read dependencies/control
plane остаются guarded, а ignored caches/build и disjoint platform/feature/
product state не входят в projection. Exact selected-lane index sealed через
path/mode/stage/blob snapshot, поэтому index-only drift не скрывается одинаковым
porcelain status; unrelated commit lane не инвалидирует.

### Пример: общая продуктовая фича

```text
$brainstorming component-training
$discovery component-training
$elaborate component-training
# человек подтверждает READY / APPROVED shared spec
$propose ios component-training
$propose android component-training
$plan ios component-training
$plan android component-training
$implement ios component-training --all
$implement android component-training --all
$verify ios component-training
$verify android component-training
$archive implementation ios component-training
$archive implementation android component-training
```

Каждая platform-ветка может идти своим темпом. Shared REQ/AC не копируются в
implementation specs: platform package ссылается на общий контракт и добавляет
только platform requirements, design и evidence.

### Пример: platform-only обслуживание

```text
$propose android build-cache-cleanup --technical-only
$plan android build-cache-cleanup
$implement android build-cache-cleanup --all
$verify android build-cache-cleanup
```

До `propose` нужно документировать `Product impact assessment: NONE` и evidence.
Флаг не является обходом product gate.

## Review, harness и evidence

`deep-code-review` всегда read-only: review/feedback/bug используют platform
identity, security запускает redacted harness scan. Findings не считаются
исправлением; отдельный fix проходит `implement → verify`.

Для изменения харнеса `$harness-change` фиксирует type/operation/scope,
канонического владельца, documentation impact и wiring cascade. `$harness-review`
объединяет deterministic lint/docs checks и read-only semantic audit. Новое
жёсткое инструктивное поведение дополнительно проходит `$writing-skills` через
RED → GREEN → REFACTOR и сохраняет test evidence.

## Явный commit flow

```text
явная просьба commit
  → явный intended path set
  → $reconcile-implementation отдельно для каждой platform/feature/change identity
  → reconciliation report
  → scoped staging разрешённого set
  → $pre-commit-check по staged index + exact intended paths
  → stable staged fingerprint: PASS + private short-lived receipt
  → runtime hook preview проверяет receipt без consumption
  → tracked Git hook one-shot потребляет receipt и повторяет integrity
  → commit в пределах исходного разрешения
```

`$pre-commit-check` не делает `git add`, commit или push. Любое изменение index
инвалидирует receipt. Runtime hooks дают ранние deny/warnings, но не заменяют
tracked Git hook, не потребляют receipt и не расширяют delivery authorization.
Exact intended set обязан совпасть со всем staged set, включая обе стороны
rename/copy; rename old/new mutable, у copy source guarded read-only, а
destination mutable и единственный требует task coverage. Extra/missing staged
path и ambiguous mutable package owner дают FAIL.
Unrelated unstaged state разрешён.

`$reconcile-implementation <platform> <feature> [--change <id>] --path ...`
также не пишет production/index/shared product: он согласует только выбранный
active package. После invalidation свежий `$verify` нужен для восстановления
terminal claim; non-terminal package после `RECONCILED` может идти в scoped
staging/pre-commit.
Reconcile использует selected lane projection: disjoint package/product/
platform dirty, index и unrelated commit допустимы, selected package/intended
paths/shared spec/rules/adapter/control plane остаются guarded.

Детали: [`deep-info.md`](deep-info.md),
[`workflow/README.md`](workflow/README.md),
[`process/flows.md`](process/flows.md) и [`AGENTS.md`](AGENTS.md).
