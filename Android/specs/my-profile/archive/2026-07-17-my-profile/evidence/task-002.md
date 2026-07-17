# task-002 — Доказательства реализации

## Итог

Граница данных профиля сохраняет распространение отмены:
`CancellationException` из HTTP-границы больше не маппится в восстановимую
ошибку отсутствия сети. Добавлена сфокусированная модульная проверка для
стандартного удалённого источника данных.

## Технические доказательства

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 1600 -- ./Android/gradlew -p Android :my-profile:testDebugUnitTest --console=plain
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform android --feature my-profile --change my-profile --task task-002 --baseline Android/specs/my-profile/changes/my-profile/evidence/scope-baseline-task-002.json --expected-sha256 c29e2dc6a9074c44f2e891383ff87d4c7f05a196b28920463d73e49b16dc956b
```
