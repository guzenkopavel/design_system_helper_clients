# iOS propose/plan — test evidence

## RED

До изменения отсутствовали portable `propose`/`plan`, platform lifecycle,
system-design, iOS architecture roles и deterministic package gate. Вызов нельзя
было однозначно направить в iOS или безопасно отклонить для Android; формат
platform package и граница shared REQ/AC не были machine-checkable.

После первой реализации independent adversarial audit обнаружил false-green:
validator возвращал `[]` для `Covers: IOS-REQ-999`, пустого Inline contract
context, Extended design из одних headings, cyclic/missing dependencies, пустого
Paths, reversed estimate `1.5–0.5`, unresolved proposal question при пустом meta
и placeholder approver/evidence. Path traversal feature/shared paths также не
имели достаточного containment gate. Эти observed failures стали RED для
текущего fix-loop.

## GREEN — structural/script evidence

| Scenario | Expected | Evidence |
|---|---|---|
| valid product-backed iOS fixture | validator принимает ровно один структурно полный package | stdlib self-test; не skill artifact run |
| missing platform | blocker, zero writes | required CLI args + manual-only skill |
| Android | explicit unsupported, zero writes | scripts return exit 4 before package access |
| DRAFT/PENDING shared product spec | blocker | validator status/approval gate |
| technical-only PRESENT/UNCERTAIN | reroute/blocker | meta gate requires `NONE` + evidence |
| plan before specified/design | blocker | lifecycle + plan gate |
| Extended iOS | common system-design + iOS architecture/SDK/verification | validator headings + iOS addendum |
| plan tasks | self-contained, one layer, ≤2d, DAG/range estimates | validator task schema/count |
| change identity | strict kebab-case; omitted downstream ID only with one active package | change-aware resolver adversarial fixtures |
| clean break | package only under `changes/<change-id>/`; no root fallback | validator lookup contract |
| no iOS codebase yet | existing vs proposed paths separated | retrieval no-hit greenfield label |

`validate-platform-change.py --self-test` содержит позитивные propose/plan
fixtures и требует RED для каждого adversarial case из audit.

Наблюдаемые structural results текущего change:

- `harness-lint.py --warn-as-error`: grade A, 0 findings;
- `quick_validate.py`: PASS для всех 8 repository skills;
- validator self-test: PASS после fix-loop; Covers проверяется только на
  declared IDs, sections/method/evidence должны быть substantive, design gate
  вычисляется по content, tasks проходят path/context/estimate/DAG gates;
- path safety fixtures: traversal/absolute feature slug и
  traversal/absolute/mismatched shared spec path отвергаются;
- Android/unknown/missing platform: exit 4/3/2 до доступа к package;
- OpenCode обнаружил все 8 repository skills по `.agents/skills`; Claude Code и
  OpenCode имеют по 8 thin commands;
- 5 новых ролей имеют parity в Codex, Claude Code, Cursor и OpenCode;
- banned-name/legacy-path scan: no matches.

## REFACTOR combinations

1. product-backed + Extended + UI: shared intake, full common system-design и
   iOS SDK/a11y/design-system gates.
2. technical-only + Quick: shared spec не нужен, но `NONE` evidence и bounded
   design N/A reason обязательны.
3. greenfield + Standard: navigator не объявляет proposed source paths
   существующими; Standard design остаётся обязательным.

## Platform evidence

Независимые dry-runs primary coordinator:

1. `propose ios token-challenge`: user claim о готовой общей спеке не заменил
   файл; отсутствующий `specs/product/token-challenge/spec.md` дал blocker, zero
   writes.
2. `propose android token-challenge`: adapter отсутствует, `NOT IMPLEMENTED`,
   zero writes.
3. `propose ios build-tooling --technical-only`: intake `Product impact: NONE`
   принят; retrieval не выдал proposed source paths за existing. Dry-run показал,
   что после gates skill создал бы только пять файлов iOS package; сами artifacts
   в этом тесте не создавались.
4. `plan ios token-challenge`: отсутствующий package/meta дал blocker, zero
   writes.

iOS structural/script evidence PASS. Android implementation intentionally
отсутствует; common contract не содержит iOS canon.

## Historical artifact-producing E2E

До change-id migration для полного lifecycle был временно создан синтетический approved shared fixture
`specs/product/harness-e2e-fixture/spec.md`, после чего последовательно запущены
`propose ios harness-e2e-fixture` и `plan ios harness-e2e-fixture`.

Первый проход дал RED: backticked platform IDs в сгенерированных артефактах не
разбирались validator-ом согласованно. После выравнивания формата ID повторный
`propose` завершился с результатом
`Platform package: VALID (propose, iOS/harness-e2e-fixture)`. `plan` и его
финальный повторный прогон завершились с результатом
`Platform package: VALID (plan, iOS/harness-e2e-fixture)`.

Наблюдаемый lifecycle package:

- `propose` создал пять platform artifacts;
- `plan` создал `plan/README.md` и `task-001.md`–`task-006.md`;
- `meta.json` перешёл в `planned`, `tasks_total` стал равен 6;
- writes были ограничены прежним feature-root package, Android не изменялся;
- после фиксации evidence shared fixture и весь временный iOS package удалены.

Текущий clean-break contract не принимает этот прежний layout. Новый active
target — `iOS/specs/<feature>/changes/<change-id>/`; propose omission по
умолчанию использует feature slug, а plan omission требует ровно один active
package. Позитивные и adversarial fixtures нового lookup входят в текущий
`validate-platform-change.py --self-test`.

## Residual limits

Machine validator проверяет структуру, containment и traceability, но не заменяет
экспертную оценку архитектурного решения. Независимый финальный harness audit
остаётся PENDING primary.
