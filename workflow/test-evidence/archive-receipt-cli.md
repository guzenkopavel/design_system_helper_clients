# Archive receipt CLI evidence

## Change plan

- **Тип:** script + phase/skill/doc
- **Операция:** modify
- **Зачем:** после successful `archive implementation --apply` не было публичного
  post-archive receipt check. Агенту приходилось импортировать внутреннюю
  функцию `validate_implementation_receipt`, а
  `validate-platform-change --mode archive` после relocation ожидаемо падал на
  отсутствующем active `meta.json`, потому что это pre-apply gate.
- **Scope:** common

## Locate

- **Затронутый flow:** `process/flows.md` → platform lifecycle →
  `archive implementation`.
- **Канонический владелец:** `workflow/scripts/archive-change.py`,
  `workflow/phases/archive.md`, `workflow/rules/archive-lifecycle.md`.
- **Placement:** canonical common script/rule/phase; portable `$archive` skill
  обновлён как runtime entry.
- **SSOT-проверка:** существующие receipt validators уже жили внутри
  `archive-change.py`; дубль не создан, добавлен только public CLI wrapper.
- **Просмотрено:** `.agents/skills/harness-change/SKILL.md`,
  `workflow/phases/harness-change.md`, `workflow/rules/runtime-adapters.md`,
  `workflow/rules/repository-documentation.md`, `process/README.md`,
  `workflow/scripts/archive-change.py`, `workflow/phases/archive.md`,
  `workflow/rules/archive-lifecycle.md`, `.agents/skills/archive/SKILL.md`,
  `workflow.md`.

## Forbidden

- **Зависимости:** product disposition продолжает ссылаться только на
  verified implementation receipt; retirement receipt остаётся tombstone-only
  evidence.
- **Инварианты:** dry-run before apply, no force/overwrite, no symlink traversal,
  no commit, platform isolation, existing receipt integrity semantics.

## Root documentation impact

- **README.md:** no-impact — top-level overview/capabilities не меняются.
- **workflow.md:** update — operational guide должен объяснить новую
  post-apply receipt command и отличие от pre-apply lifecycle validator.
- **deep-info.md:** no manual impact — script inventory остается тем же; generated
  projections проверяются через `harness-docs.py`.

## Evidence

```text
rtk python3 -m py_compile workflow/scripts/archive-change.py

rtk python3 workflow/scripts/archive-change.py --self-test
archive-change self-test: PASS (implementation/product gates, isolation, collision safety)

rtk python3 workflow/scripts/archive-change.py receipt --platform android --feature user-profile-auth --receipt Android/specs/user-profile-auth/archive/2026-07-17-user-profile-auth/archive-receipt.json
Archive receipt: VALID
- Android/specs/user-profile-auth/archive/2026-07-17-user-profile-auth/archive-receipt.json (implementation)

rtk python3 workflow/scripts/harness-docs.py check --json
{"status":"PASS", ...}

rtk python3 workflow/scripts/harness-lint.py --json
{"grade":"A","critical":0,"warnings":0,"findings":[]}
```

## Platform evidence

- **iOS:** affected by common receipt CLI; covered by `archive-change.py
  --self-test` fixture for verified and retirement receipts.
- **Android:** affected by common receipt CLI; covered by `archive-change.py
  --self-test` fixture and real `user-profile-auth` archive receipt command.

## Residual risk

`receipt` mode intentionally accepts only safe repo-relative receipt paths. It
does not replace dry-run/apply gates and does not validate active packages.
