# Android Verify и implementation archive

## RED

До изменения Android adapter содержал только
`propose → plan → implement`:

```text
validate verify: exit 4, NOT IMPLEMENTED
capture verification state: exit 2, NOT IMPLEMENTED
archive implementation dry-run: exit 2, NOT IMPLEMENTED
Harness lint: grade A (0 critical, 0 warnings)
```

Active package и его pending verification artifact не изменялись.

## Compatibility decision

Adapter получил canonical capabilities
`propose, plan, implement, verify, archive-implementation` и ordered verify
profile только из уже существующих:

```text
workflow/rules/test-execution.md
workflow/rules/verification-matrix.md
```

Новый rule не добавлялся в `rule_files`, поэтому lifecycle union остаётся
совместимым с sealed `client-bootstrap/initial-scaffold` selection. Общий
`workflow/rules/verification-evidence.md`, общий verify phase и Android verify
addendum загружаются напрямую state capture и fingerprinted как обязательные
terminal contracts вне adapter union. Их отсутствие блокирует capture; если
общий evidence rule уже выбран платформой, вход дедуплицируется.

Compatibility proof:

```text
Platform package: VALID (implement, Android/client-bootstrap/initial-scaffold)
```

## GREEN

- `Android/workflow/phases/verify.md` обнаруживает wrapper/settings/modules/
  plugins/tasks/variants/commands/infrastructure, не предполагая module, task,
  Compose, Emulator или system Gradle;
- unavailable required infrastructure даёт `UNKNOWN`, nonzero discovered
  command — `FAIL`, fresh concrete evidence — `PASS`;
- verifier production read-only; diagnostician не repair;
- `Android/workflow/phases/archive.md` использует общий dry-run/apply,
  fingerprint, collision rollback, receipt и tombstone contract;
- product archive и shared product package не изменены;
- deep review после отдельного fix возвращает `verify android`, но остаётся
  read-only до отдельного Implement + Verify.

Current package read-only pressure:

```text
verify: exit 2, 8 verification/content blockers; NOT IMPLEMENTED отсутствует
capture state dry-run: exit 0, fingerprint produced
archive dry-run: exit 2, verified-state blockers; NOT IMPLEMENTED отсутствует
```

## Pressure matrix

| Scenario | Evidence |
|---|---|
| capability missing/reordered | validator/lint self-tests reject dependency/order |
| verify profile misses matrix or adds another rule | Android profile mutation rejected |
| selected scope dependency broken | Android dependency mutation rejected |
| iOS rule leaks into Android adapter/addendum | lint critical |
| fixed Kotlin/coverage/Gradle task assumption | lint mutation/scan critical |
| production/task/plan/rule baseline mutation during Verify | implementation-scope self-test rejects |
| required infra unavailable | exact `UNKNOWN`, terminal state blocked |
| discovered command nonzero | exact `FAIL`, recovery path |
| every row fresh PASS | state capture + terminal validator path |
| stale fingerprint | capture/archive self-tests reject |
| common evidence/common phase/iOS or Android addendum changed | fingerprint changes; exact restore restores it |
| mandatory terminal contract missing | state capture fails closed |
| archive collision or injected pre/post move failure | rollback preserves pre-call tree |
| receipt/integrity mutation | archive/product disposition validation rejects |

Archive self-test использует отдельный Android-native fixture с `.kt`, `.kts`,
Android-owned rules/context suffixes и Android adapter; iOS и Android archive
результаты проверяются независимо.

## Final regression

```text
Platform package: VALID (implement, iOS/client-bootstrap/initial-scaffold)
Platform package: VALID (implement, Android/client-bootstrap/initial-scaffold)
validate-platform-change self-test: PASS
validate-implementation-scope self-test: PASS
capture-verification-state self-test: PASS
archive-change self-test: PASS
Harness lint: grade A (0 critical, 0 warnings)
harness-lint self-test: PASS
Harness security audit: PASS (complete coverage, 0 findings)
```

iOS adapter/profile/addenda не менялись. Android current package, shared product
package и lifecycle-owned pending verification artifact также не менялись;
terminal commands выше выполнялись только в read-only validation/dry-run mode.
