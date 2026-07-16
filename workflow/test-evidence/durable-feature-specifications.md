# Durable feature specifications — RED → GREEN → REFACTOR

## Change plan

- **Тип / операция:** rule + phase + skill + script + documentation, modify.
- **Scope:** cross-platform (`common`, iOS, Android).
- **Failure mode:** после archive оставались только tombstones и immutable
  change history; future agents не имели current product/platform contract.
- **Канонические владельцы:** `workflow/rules/archive-lifecycle.md` и
  `workflow/rules/specification-layers.md`.
- **Инварианты:** single writer, no commit, immutable archives, atomic rollback,
  historical receipt compatibility, product review isolation.

## Соседние репозитории

- Jourio: `process/flows.md:89` задаёт archive как merge change delta в
  feature-root `SPECIFICATION.md`; реальные feature roots одновременно содержат
  `SPECIFICATION.md` и `archive/<date-change>/`.
- elph-nova-ios: `AGENTS.md:78` определяет current specification в
  `docs/features/<Feature>/SPECIFICATION.md`, а историю — в соседнем `archive/`;
  `README.md:58` описывает archive как merge в `SPECIFICATION.md` + history.

Выбран тот же принцип, адаптированный к shared product и двум независимым
platform lifecycle: archive — immutable evidence, feature-root
`SPECIFICATION.md` — current baseline.

## RED

До изменения проверены три доставленных app-shell surfaces:

```text
test ! -e specs/product/app-shell/SPECIFICATION.md
test ! -e iOS/specs/app-shell/SPECIFICATION.md
test ! -e Android/specs/app-shell/SPECIFICATION.md
```

Все проверки отсутствия прошли: product root содержал только archived
`spec.md` tombstone, platform roots — только `changes/app-shell/ARCHIVED.md` и
полные archives. `archive-change.py --self-test` подтверждал старый контракт:
после apply требовался tombstone, но durable baseline не проверялся.

## GREEN

Тот же сценарий теперь требует и получает:

- `specs/product/app-shell/SPECIFICATION.md` — нормализованный доставленный
  product contract с `REQ-1`–`REQ-6`, `AC-1`–`AC-5` и evidence обеих платформ;
- `iOS/specs/app-shell/SPECIFICATION.md` — current iOS contract из immutable
  `implementation-spec.md` и receipt;
- `Android/specs/app-shell/SPECIFICATION.md` — симметричный Android contract;
- новый completed archive атомарно публикует baseline; implementation receipt
  schema v2 связывает archived source SHA-256 и published-at-time bytes;
- исторические receipt v1 остаются валидными и не зависят от будущей замены
  current baseline.

Команды:

```text
python3 workflow/scripts/archive-change.py --self-test
python3 workflow/scripts/validate-product-spec.py --self-test
```

Обе завершились `PASS`.

## REFACTOR и pressure scenarios

1. **Completed product publish:** approved package перемещён целиком,
   `retirement-request.json` неизменяемо сохранён, tombstone создан, полный
   current baseline опубликован; fault после baseline write восстанавливает
   exact прежнее дерево.
2. **iOS и Android implementation publish:** обе platform fixtures публикуют
   feature-root baseline; receipt v2 проверяет archive source/hash/published
   bytes. Изменение current baseline после этого не инвалидирует historical
   receipt.
3. **Replace + rollback:** существующие product/platform baseline bytes
   заменяются только на success; injected pre/post move, state, receipt,
   baseline и tombstone failures возвращают exact prior bytes/absence.
4. **Retired candidate pressure:** `cancelled` сохраняет прежний delivered
   baseline byte-for-byte; `superseded` без baseline не создаёт ложный current
   contract.
5. **Fingerprint/read-only pressure:** создание и изменение root
   `SPECIFICATION.md` не меняет candidate product fingerprint; symlink и
   non-regular source/baseline collision блокируются preflight.
6. **Historical compatibility:** receipt v1 из app-shell остаётся валидным;
   новые receipts используют v2 binding без требования вечного совпадения с
   current root baseline.
7. **Archive path topology:** iOS и Android implementation archive блокируют
   symlink archive namespace; dangling exact target считается collision.
   Product `_archive` проверяется симметрично. Apply-pressure подтверждает
   неизменность всего repo tree и отдельного дерева вне intended namespace.
8. **Self-contained source/receipt:** nested implementation/product symlink на
   mutable external bytes и product FIFO блокируются до validator/move;
   `archive_integrity` не следует symlink/special entries. Receipt, archived
   `meta.json`, verification state и archive-namespace symlink также дают
   fail-closed error, включая product disposition path.
9. **Schema-aware metadata:** v2 игнорирует `.DS_Store`; v1 без записанного
   metadata сохраняет совместимость при позднем stray file; v1 с записанным
   `.DS_Store` проходит до mutation этого файла и затем даёт integrity mismatch.
10. **Product wiring:** generated product-backed platform baseline содержит
    exact `specs/product/<feature>/SPECIFICATION.md` и объясняет переход от
    archive provenance до completed product publication. Helper pressure для
    `technical-only` не содержит product path или ложной shared-ссылки.
11. **Retirement request path:** explicit request symlink на mutable JSON и
    default request через symlink parent блокируются по lexical path до чтения;
    repo/outside signatures остаются неизменными. Request также имеет regular
    non-symlink и 1 MiB bounds.
12. **Exact receipt exclusion:** только root `archive-receipt.json` исключён из
    self-manifest. Nested `evidence/archive-receipt.json`, добавленный после
    archive, даёт mismatch; nested same-name file, существовавший при receipt
    creation, входит в manifest и его mutation также даёт mismatch.

## Root documentation impact

- **README.md: update** — новый visible feature-root knowledge surface.
- **workflow.md: update** — archive output и starting baseline меняют
  operational flow.
- **deep-info.md: update** — schema/ownership inventory расширены; generated
  blocks обновляются только через `harness-docs.py render`.

## Финальная проверка

- `archive-change.py --self-test`: PASS, включая publish/replace/rollback,
  cancellation/supersede, baseline и archive-namespace symlink/dangling-target
  collisions, recursive source/receipt symlinks, special nodes, schema-aware
  `.DS_Store`, отсутствие outside reads/writes и historical receipt pressure.
- `validate-product-spec.py --self-test`: PASS, baseline не меняет fingerprint.
- `validate-platform-change.py --self-test`: PASS.
- Real v0 iOS:
  `validate-platform-change.py --platform ios --feature client-bootstrap
  --change initial-scaffold --mode implement`: VALID.
- Real v0 Android: симметричная команда с `--platform android`: VALID.
- Оба app-shell receipt v1 проверены текущим validator: errors `[]`.
- `artifact_language.py --self-test` и отдельная проверка трёх восстановленных
  Markdown baselines: PASS.
- `find-platform-context.py --self-test`, `harness-docs.py --self-test`,
  `py_compile` затронутых scripts и `git diff --check`: PASS.
- `harness-docs.py render`: idempotent, `changed: []`; read-only `check --json`:
  PASS, errors `[]`.
- `harness-lint.py --json`: grade A, critical `0`, warnings `0`, findings `[]`.
- SHA-256 immutable app-shell sources после восстановления совпадают с исходными:
  product `2927db...`, iOS `19dd6d...`, Android `a28adac...`.

## Остаточные ограничения

- Восстановленный product app-shell baseline нормализует доставленное состояние
  и намеренно не меняет исторический archive с противоречивым pre-delivery
  `DRAFT` текстом.
- Semantic merge нескольких concurrent candidate contracts не выполняется:
  каждый новый candidate обязан быть полным post-change contract и проходит
  обычные Propose/Elaborate gates до публикации.
