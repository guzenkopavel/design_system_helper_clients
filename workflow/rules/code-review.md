# Code review

Deep review оценивает observable behavior и contract-fit, а не стиль ради
стиля. До findings прочитать выбранный shared/platform contract, package meta,
tasks и current code. Accepted decisions — context, не иммунитет от проверки.

## Три независимых прохода

1. **Pass A — contract compliance.** Для каждого применимого REQ/AC/задачи дать
   `PASS|FAIL|UNKNOWN` и current-code evidence. Не выдумывать требования.
2. **Pass B — platform/rule scan.** Прочитать каждый scoped file целиком и
   применить package `applicable_rule_files` либо явно перечисленные risk
   lenses. Pattern без call-site/context evidence не является confirmed bug.
3. **Pass C — trace-through.** Проследить decision/state/data-flow от input до
   observable output: ветки, mapping полей/ID, terminal/error/cancellation paths,
   call sites и boundary integration. Фиксировать unreachable, data-loss,
   lying-reference, stuck-state и contract-divergence только с evidence.

После passes dedupe findings по root cause/location. Fresh-eyes reviewer получает
минимальный handoff без предыдущих findings. Если та же сессия выполняет второй
проход, independence помечается `UNAVAILABLE`.

## Feedback triage

Каждый внешний finding проверяется против current code независимо от авторитета
источника. Допустимые статусы:

- `accepted` — observation и impact подтверждены;
- `rejected` — доказанный false positive/out-of-scope/конфликт с каноном;
- `duplicate` — тот же root cause уже представлен;
- `needs-evidence` — данных недостаточно для решения.

Performative agreement запрещён. Accepted не означает applied/fixed.

## Finding schema

```text
DCR-N — <title>
Severity: blocker|high|medium|low
Confidence: high|medium|low
Status: confirmed|needs-evidence|accepted|rejected|duplicate
Location: <exact path>:<start>-<end>
Observation: <current-code fact>
Evidence: <call-chain/runtime/contract proof>
Violated contract/rule: <ID/path or NONE>
Impact: <observable or maintenance risk>
Lifecycle route: propose|plan|implement|verify-ios|none
```

Finding без exact location/evidence остаётся `needs-evidence`. Optional
improvements и open questions отделять от findings.
