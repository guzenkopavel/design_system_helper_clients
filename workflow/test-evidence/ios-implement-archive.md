# iOS implement/verify/archive — test evidence

## RED

До изменения portable `implement` и `archive` skills отсутствовали;
`validate-platform-change.py` принимал только `propose|plan` и отвергал
`implement|archive` как неизвестные mode; `archive-change.py` отсутствовал.
Platform package identity была только feature-level, task completion и fresh
verification не имели machine-readable terminal gates.

Свежий forward-test после первой GREEN-версии обнаружил пять fail-open gaps:

- Verify не выставлял candidate `status: verified` и не определял persisted
  FAIL/UNKNOWN recovery с reopened tasks;
- mixed allowed+protected Paths проходили scope guard, baseline/evidence scope
  был шире task identity;
- product reference scan видел только conventional roots и игнорировал
  `status: archived` внутри active changes;
- fingerprint не включал `verification.md` и evidence set/content;
- archive rollback оставлял созданные текущим вызовом empty parent directories.

Эти наблюдения стали RED для второго fix-loop.

Финальный bounded forward-test обнаружил recovery-closure gap: upstream task
reopen не возвращал в pending уже выполненные downstream dependents, а успешный
repair оставлял старые FAIL/PASS rows активными. Это нарушало DAG и не давало
machine-coherent пути обратно к fresh Verify.

Финальный read-only audit дополнительно обнаружил четыре fail-open границы:
ancestor task path мог охватить protected root; archive не сохранял
самодостаточное криптографически связанное доказательство; product disposition
доверял одному `meta.json`; partial/сломанные tombstones внутри active namespace
не перечислялись fail-closed. Эти случаи добавлены как RED до исправления.

## GREEN

Реализован clean-break identity
`<platform>/specs/<feature>/changes/<change-id>/` без legacy-root fallback.
Lifecycle расширен до `implementing`, `verified`, `archived`; Android и unknown
platform проходят adapter gate до любых writes.

Фактические deterministic results:

- `python3 workflow/scripts/validate-platform-change.py --self-test` →
  `PASS (change-aware lifecycle and adversarial gates)`;
- `python3 workflow/scripts/validate-implementation-scope.py --self-test` →
  `PASS (ready deps, allowed paths, dirty preservation)`;
- `python3 workflow/scripts/capture-verification-state.py --self-test` →
  `PASS (deterministic and stale-sensitive)`;
- `python3 workflow/scripts/archive-change.py --self-test` →
  `PASS (implementation/product gates, isolation, collision safety)`;
- `python3 workflow/scripts/harness-lint.py --warn-as-error` → grade A,
  0 critical, 0 warnings;
- `quick_validate.py` через `uv run --with pyyaml` → `Skill is valid!` для
  изменённых `implement`, `verify` и `archive` skills.

Self-tests используют временные `--root` repositories и не создают реальные
platform packages. Implementation archive доказывает verified/all-done/PASS/
freshness gates, shared-spec provenance, isolated move, receipt и tombstone.
Product archive сначала получает RED на active reference, затем после genuine
iOS и Android implementation archives проходит dry-run/apply, переносит пакет
как unit и оставляет exact-path product tombstone.

## REFACTOR pressure combinations

1. `planned` + ready task + done dependencies + declared production path:
   scope baseline/check разрешает каждый task Path, exact task evidence и exact
   canonical baseline. Mixed protected Path, arbitrary evidence, external/
   traversal baseline, ancestor Path над protected root и post-baseline
   unrelated/protected change дают RED; pre-existing dirty state сохраняется.
2. terminal FAIL upstream row сохраняет exact meta/problems, reopen напрямую
   затронутые task-001/task-003 и transitive dependent task-002, после чего
   derived `tasks_done` равен нулю и recovery валиден. Любая оставленная done
   task из полного closure даёт DAG RED; unmapped problem требует plan repair.
   После успешного repair старые rows/meta сбрасываются в pending/null,
   historical evidence сохраняется и mixed done/pending Implement state
   валиден. Затем closure завершается, all-done/pending Implement проходит, а
   fresh all-PASS Verify выставляет candidate verified. Initial baseline не
   разрешает verification.md; recovery FAIL/UNKNOWN baseline разрешает только
   его exact reset.
3. all tasks done + terminal PASS rows + затем изменение realized source,
   verification row, evidence content или evidence set: fingerprint становится
   stale и `verify/archive` получает RED до fresh rerun.
4. verified implementation package + fresh proof: implementation archive меняет
   только выбранный package/archive/tombstone и не изменяет shared source;
   collision/traversal блокируются. Shared snapshot хранится как provenance вне
   fingerprinted evidence; исходный fingerprint повторно проверяется после
   relocation. Версионированный receipt связывает identity, terminal state и
   SHA-256 manifest. Fault injection до/после `move`, на state-check и после
   создания receipt отдельно доказывает exact pre-call tree, включая удаление
   только новых empty archive parents и transient provenance/receipt.
5. product retirement request + active implementation reference или missing
   Android disposition: archive получает RED. После explicit per-platform
   dispositions и отсутствия active refs fake narrative/minimal receipt всё ещё
   получает RED. GREEN требует созданные implementation archive операцией iOS и
   Android
   `<Platform>/specs/<feature>/archive/<archive-id>/archive-receipt.json` с
   согласованными meta/state/manifest; adapter для исторического Android
   evidence не требуется. Traversal, directory/meta и active tombstone paths
   отвергаются. Nonconventional adapter package root, archived meta, partial
   child, extra tombstone file и broken tombstone target внутри active changes
   отдельно дают RED; genuine receipt-backed tombstones проходят.
6. `reason: completed` + DRAFT/PENDING product spec получает RED даже с реальными
   platform archives. Тот же draft допустим для explicit `cancelled`; после
   восстановления `READY`/`APPROVED` completed dry-run/apply проходит.
7. Android/unknown implementation invocation: adapter отсутствует, поэтому
   resolver возвращает `NOT IMPLEMENTED` до package discovery и writes.

Наблюдаемые CLI blockers: Android `implement` и implementation archive —
`NOT IMPLEMENTED`, unknown verify — `NOT IMPLEMENTED`, traversal feature для
archive — strict kebab-case blocker; все сообщения явно фиксируют отсутствие
writes.

## Platform evidence

- iOS adapter объявляет broad greenfield production ownership `iOS` с явными
  exclusions/protected roots `iOS/specs` и `iOS/workflow`, archive namespace,
  rule files и iOS addenda.
- Android получает общий contract, skills и runtime discovery, но без adapter;
  implementation lifecycle остаётся `NOT IMPLEMENTED`. Product archive требует
  explicit Android disposition и genuine receipt evidence, поэтому отсутствие
  adapter не превращается в silent success. Temporary self-test adapter нужен
  только для создания реального Android archive fixture и удаляется перед
  product disposition validation.

## Residual limits

Machine gates доказывают identity, structure, scope, task state, evidence paths,
freshness и collision safety. Они не доказывают качество платформенной
архитектуры или достаточность выбранных сценариев: это остаётся ответственностью
platform lenses и свежего read-only verifier. Финальный harness audit фиксируется
отдельно после полного lint/runtime validation. Первый read-only audit закрыл
rollback finding; последующий fresh forward-test обнаружил A–E gaps из RED
выше. После финального fix-loop четыре self-tests снова GREEN, lint grade A,
`py_compile` и changed-skill validation PASS.
