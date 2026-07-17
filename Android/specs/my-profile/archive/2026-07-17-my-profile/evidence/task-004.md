# task-004 — Доказательства реализации

## Итог

Корневая композиция приложения оставлена в роли связывания зависимостей:
`MainActivity` создаёт repository и передаёт callback очистки сессии, а
состояние профиля, восстановление и обработка выхода принадлежат `ProfileRoute`
в модуле `:my-profile`.

## Технические доказательства

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420 --stall-seconds 90 --max-output-lines 2400 -- ./Android/gradlew -p Android :app-shell:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug --console=plain
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform android --feature my-profile --change my-profile --task task-004 --baseline Android/specs/my-profile/changes/my-profile/evidence/scope-baseline-task-004.json --expected-sha256 6e0d38ad655e3dc6da1cf056bb2a446dbbb1bb03b242706e18c99543deeb208c
```
