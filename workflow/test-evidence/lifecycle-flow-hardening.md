# Lifecycle flow hardening — test evidence

## Change plan

- **Тип/операция:** modify rule, phase, skill, script, template, process и docs.
- **Scope:** cross-platform.
- **Канонические владельцы:** product readiness/review/language, platform Plan,
  implementation scope baseline, archive lifecycle и verification evidence в
  `workflow/`; platform adapters остаются thin.
- **Инварианты:** single writer, без production/app-shell/spec package writes,
  без staging/commit/push, общий SSOT и отдельное iOS/Android evidence.
- **Agent roster:** no-impact — новые роли не добавлялись.
- **Runtime adapters:** no-impact — invocation/capabilities и platform-specific
  tooling не изменились.
- **Platform addenda:** no-impact — новые контракты одинаковы для iOS/Android;
  native commands не добавлялись.

## RED

На исходном коде воспроизведены шесть классов отказа:

1. Product validator принимал `Status: READY` при противоречащем DRAFT тексте
   Readiness Decision.
2. Plan `Paths` принимал protected lifecycle ref `iOS/specs/.../platform-ux.md`;
   ошибка обнаруживалась только перед Implement.
3. Английское natural-language предложение проходило при добавлении длинного
   русского padding в тот же block.
4. Android task baselines включали тысячи ignored `.opencode/node_modules` и
   build/cache paths.
5. Default `archive-request.json` внутри active product package менял subject
   fingerprint и делал шесть review verdicts stale.
6. Один составной AC позволял соседнему/агрегированному PASS скрывать
   ненаблюдённые accessibility/appearance dimensions.

## GREEN

- `validate-product-spec.py` требует exact coherent `READY/none`, terminal
  Client Readiness, `None` Open Questions и одну unique
  `Verification dimension` на каждый atomic AC; product Markdown и authored
  verdict/finding JSON проходят общий language helper.
- `validate-platform-change.py --mode plan` разделяет writable `Paths` и
  immutable `Read-only context`, применяет adapter boundaries, classification,
  duplicate/ancestor-overlap gates до `planned`.
- `artifact_language.py` проверяет отдельные sentences и не позволяет русскому
  padding компенсировать English prose; exact SDK/API/command/path/ID tokens
  остаются разрешёнными.
- `validate-implementation-scope.py` пишет schema v2 с algorithm
  `git-visible-v1`: tracked + non-ignored untracked guarded, ignored cache/build
  исключены; отдельный `git-ls-files-stage-v1` projection сравнивает exact
  path/mode/stage/blob и блокирует index-only MM drift.
- Default product retirement request перенесён в
  `specs/product/_retirement-requests/<feature>/<date-feature>.json`; apply
  атомарно сохраняет exact validated `retirement-request.json` внутри product
  archive; reserved collision и post-copy/tombstone faults возвращают exact tree.
- Verify contract требует exact common `NATIVE-*` set, отдельный structured JSON
  observation record и concrete underlying refs каждой atomic obligation;
  row/record mismatch и unobserved dimension блокируют PASS. Native non-PASS
  маппится на sealed `ui` tasks и dependent closure.
- Product approval/UX N/A и retirement narratives проверяются общим language
  helper; exact names/paths/enums остаются разрешёнными.
- Все новые platform authored-meta language и `NATIVE-*` gates ограничены
  current v1. Real registry-anchored iOS/Android
  `client-bootstrap/initial-scaffold` проходят read-only mode=implement по
  exact v0 hashes без retrofit.

## REFACTOR pressure matrix

1. Product: READY coherence, duplicate/missing AC dimension, stale receipt,
   Russian authored JSON и English+Russian padding.
2. Plan: valid production Paths, protected path в Paths, тот же path в
   Read-only context, wrong existing/proposed classification, duplicate и
   ancestor overlap.
3. Baseline: ignored `node_modules/build` отсутствуют, видимый unrelated file,
   status drift и exact index-only MM blob drift блокируются в task/verify;
   SHA token нельзя подделать.
4. Archive: missing/malformed request блокируется, external default не меняет
   product fingerprint, validated bytes копируются атомарно, reserved collision
   и injected pre/post-copy/tombstone faults полностью откатываются.
5. Verify: missing native obligation и PASS row→UNKNOWN record блокируются;
   PASS/FAIL требуют raw/non-observation underlying evidence, one-way
   cross-record и A↔B observation cycles блокируются, recovery выбирает реальные
   `ui` tasks.
6. Language: English approval evidence, UX `NOT APPLICABLE` rationale и
   retirement approval narrative блокируются без дублирования helper logic.
7. Archive override: pre-reviewed internal request блокируется до mutation;
   subject fingerprint и exact source tree остаются неизменными.
8. Legacy: оба real adapter v0 packages проходят exact compatibility path;
   English historical `impact_evidence` и отсутствие native rows не блокируют.

## Root documentation dispositions

- **README.md:** `no-impact` — capabilities, roots и top-level entrypoints не
  изменились; `harness-docs render` не изменил README generated block.
- **workflow.md:** `update` — описаны READY coherence/atomic evidence,
  `Paths`/`Read-only context`, git-visible baseline и external retirement request.
- **deep-info.md:** `update` — обновлены schema/validator/archive inventory и
  durable request evidence; generated inventory обновляется render.

## Platform evidence

- **iOS:** общий validator прогоняется с real iOS adapter; synthetic pressure
  подтверждает protected `iOS/specs` boundary и допустимый read-only ref.
- **Android:** общий validator прогоняется с real Android adapter; synthetic
  baseline подтверждает отсутствие ignored `node_modules/build` и сохранение
  unrelated visible guard.

## Проверки

- `python3 -m py_compile` для семи затронутых Python modules: PASS.
- `artifact_language.py`: self-test PASS.
- `validate-product-spec.py`: self-test PASS.
- `validate-platform-change.py`: self-test PASS, включая отдельные synthetic
  pressure с real iOS/Android adapter boundaries и read-only exact v0 package
  assertions.
- Explicit real validation:
  `validate-platform-change.py --platform ios|android --feature client-bootstrap
  --change initial-scaffold --mode implement`: оба `VALID`.
- `validate-implementation-scope.py`: self-test PASS.
- `archive-change.py`: self-test PASS.
- Dependent self-tests `find-platform-context.py`, `pre-commit-check.py`,
  `reconcile-implementation.py`, `capture-verification-state.py`: PASS.
- `harness-lint.py --self-test`: PASS (exit 0).
- `harness-docs.py --self-test`: PASS, включая exclusion transient
  `workflow/archive-requests/` из inventory.
- `git diff --check`: PASS.
- `harness-docs.py render`: первый post-inventory render изменил только generated
  block `deep-info.md`; финальный idempotent render сообщил `changed: []`.
- `harness-docs.py check --json`: PASS, errors `[]`.
- `harness-lint.py --json`: grade `A`, critical `0`, warnings `0`, findings `[]`.

Harness auditor выполняется отдельно от implementation-writer.

## Остаточные ограничения

Machine gate проверяет атомарность через уникальную explicit dimension и exact
coverage, но смысловую корректность формулировки outcome по-прежнему подтверждают
шесть isolated product review lenses и human approval.
