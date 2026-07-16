# Root project documentation

## Change plan

- **Тип:** doc + rule + phase + script.
- **Операция:** add + modify.
- **Scope:** common; iOS и Android claims проверяются отдельно.
- **Канон:** `workflow/rules/repository-documentation.md`.
- **Runtime/role impact:** новые skill, role и runtime wrapper не требуются;
  flow принадлежит существующим `harness-change` и `harness-review`.

Root documentation impact:

- **README.md:** `update` — убрать stale platform claim, добавить project roots,
  entrypoints и derived capability matrix;
- **workflow.md:** `update` — новый beginner-friendly operational guide;
- **deep-info.md:** `update` — новый exhaustive wiring/inventory reference.

## RED

До изменения:

```text
workflow.md: missing
deep-info.md: missing
README.md: Android описан как unsupported
harness-lint.py: grade A, documentation gap не обнаружен
```

Это позволяло capability/runtime/ownership prose расходиться с действующим
харнесом без machine finding.

## GREEN

Добавлены exact root docs, common documentation rule и stdlib
`workflow/scripts/harness-docs.py`. Checker выводит deterministic JSON, ничего
не пишет в `check`, а `render` меняет только пять exact generated blocks:

- README capability matrix;
- workflow skill matrix;
- deep-info semantic wiring;
- deep-info file inventory;
- deep-info runtime parity.

Inventory читает filesystem, включая untracked harness files текущего change,
но исключает native source/build/cache, transient specs и license bodies.

## Pressure matrix

| Давление | Ожидаемый результат |
|---|---|
| exact doc missing или case mismatch | FAIL до чтения stale projection |
| marker missing/duplicate/malformed | FAIL |
| generated block edited manually | stale FAIL |
| skill/phase/rule/script добавлен | inventory/wiring stale до render |
| platform addendum добавлен | отдельный platform inventory stale |
| runtime binding добавлен | runtime inventory/parity stale |
| platform capability изменён | README capability block stale |
| broken command/role binding, JSON или frontmatter | fail-closed |
| render manual prose | bytes вне markers не меняются |
| повторный render | idempotent, zero changed docs |
| transient package/native file | inventory остаётся fresh |
| `.DS_Store`, `Thumbs.db` или `desktop.ini` в harness root | metadata исключается и не stale-ит docs |
| stable product/iOS/Android spec schema index | все три `README.md` входят в inventory раздельно |
| iOS/Android adapter/addendum | покрываются раздельными строками |
| broken local link или local absolute/source name | FAIL |

Semantic pressure дополнительно сверяет canonical `writes_artifacts` с
non-PASS recovery: Verify может менять `verification.md`, evidence/meta и
переоткрывать только `plan/task-NNN.md`, но не production. Manual reference
разделяет ownership snapshot: `plan/rule-selection.json` хранит scopes, exact
rules и их hash, а semantic adapter projection принадлежит verification-state
fingerprint. Product archive описывается без несуществующего receipt: он
перемещает retired package и оставляет `spec.md` tombstone; receipt создаёт
только implementation archive.

## REFACTOR и acceptance

`harness-lint.py` вызывает docs checker non-recursively. `harness-review` и
`harness-auditor` дополняют structural PASS semantic проверкой audience layers,
capabilities, invocation, ownership и write/evidence claims.

Финальные machine outputs и coverage counts фиксируются в отчёте change после
всех wiring правок, повторного render и platform package validation.
