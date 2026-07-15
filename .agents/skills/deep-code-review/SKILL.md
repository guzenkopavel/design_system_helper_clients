---
name: deep-code-review
description: Выполнить единый read-only deep review, triage feedback, доказательное bug investigation или security audit. Использовать только при явном `$deep-code-review`; fixes и lifecycle mutations запрещены.
---

# Deep Code Review

Полностью выполнить [`workflow/phases/deep-code-review.md`](../../../workflow/phases/deep-code-review.md)
и выбранный mode rule. Перед действиями валидировать invocation через
`workflow/scripts/validate-deep-code-review.py`.

Поддерживаются только `review`, `feedback`, `bug`, `security` и публичный syntax
из phase. `fix`, `--fix`, unsafe path, ambiguous identity и platform omission
блокируются до чтения scope. Skill read-only: не изменять production, specs,
package, tasks, evidence/meta; не запускать lifecycle skills и не делать
commit/push.

После успешной invocation validation и до review обязательно выполнить
`workflow/scripts/deep-code-review-readonly-guard.py start`. Сохранить opaque
token только для post-check. Перед любым финальным ответом во всех modes
выполнить `check <token>`. Только guard `PASS` разрешает valid report и `No edits
made`; `INVALID`/`UNKNOWN` делает review недействительным, запрещает
fixed/verified claims и не разрешает revert. Guard state приватный, ephemeral,
`0600`, вне repo; repository artifacts по-прежнему запрещены.

В `feedback` file report не читать напрямую. Взять `report_sha256` и
`report_size` из validator result и после guard `start` вызвать только
`workflow/scripts/read-deep-code-review-report.py` с exact expected identity.
Reader mismatch/race блокирует review до triage.

Применить platform addendum для `review|feedback|bug`. Если после отчёта нужен
fix, вернуть exact lifecycle route из phase. Android никогда не называть
fixed/verified: terminal Verify unavailable.
