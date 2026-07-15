---
phase: deep-code-review
writes_artifacts: []
requires_verification: focused
recommended_roles:
  - deep-code-reviewer
  - bug-investigator
  - security-reviewer
---

# Phase: Deep Code Review

Единая read-only фаза для независимого review, triage входящего feedback,
доказательного bug investigation и security audit харнеса.

## Public contract

```text
deep-code-review review <platform> <feature> [--change <change-id>] [--against <git-ref>|--paths <...>]
deep-code-review feedback <platform> <feature> [--change <change-id>] --report-source <stdin|safe-repo-path>
deep-code-review bug <platform> <feature> [--change <change-id>] <symptom-or-finding>
deep-code-review security [--json]
```

`review`, `feedback`, `bug` требуют `ios|android` и feature. `--change`
разрешается явно либо выводится только при одном active package. Несколько
active packages без `--change` — ambiguous identity и blocker. `--against` и
`--paths` взаимоисключающие. Report/path остаётся внутри repo; absolute path,
`..`, secret/key path и отсутствующий report запрещены до чтения.
`review --paths` после resolve adapter обязан оставаться внутри его
`platform_root`; cross-platform path запрещён. `feedback --report-source`
принимает только bounded regular UTF-8 file либо `stdin` и до чтения отклоняет
adapter `pre_commit.secret_globs`.

Режим `fix`, флаг `--fix`, неизвестный mode и platform omission блокируются до
любых действий. Вход валидируется через
[`validate-deep-code-review.py`](../scripts/validate-deep-code-review.py).

## Общие инварианты

- `writes_artifacts: []` означает отсутствие repository artifacts: не изменять production, package, task, evidence,
  verification или meta и не создавать durable review report.
- После invocation validation и до review запустить
  `python3 workflow/scripts/deep-code-review-readonly-guard.py start`. Его
  opaque token указывает на private `0600` ephemeral state вне repo, не является
  repository artifact и не должен публиковаться.
- Перед любым финальным выводом, включая `security`, обязательно запустить
  `python3 workflow/scripts/deep-code-review-readonly-guard.py check <token>`.
  Только `PASS` делает report валидным; `INVALID` mutation или `UNKNOWN`
  coverage блокируют valid report. Guard ничего не revert и удаляет private
  state после valid check.
- Не запускать автоматически manual-only `propose`, `plan`, `implement`,
  `verify`, `archive`, commit или push.
- Читать current code и current contracts; prior narrative не является proof.
- Использовать platform addendum и только applicable rule/risk lenses.
- Если runtime не даёт независимый subagent, выполнить passes последовательно в
  основной сессии и явно написать: `Fresh-eyes independence: UNAVAILABLE`.

## Mode routing

### `review`

Передать роли `deep-code-reviewer` exact scope. Она выполняет независимые Pass
A/B/C из [`code-review.md`](../rules/code-review.md), затем synthesis. Для
fresh-eyes передать только paths, contract/AC references и задачу поиска
регрессий; previous findings/решения не передавать. Same-context fallback не
называть независимым.

### `feedback`

Для file source validator возвращает `report_sha256` и `report_size`. После
guard `start` читать report только через
`python3 workflow/scripts/read-deep-code-review-report.py <path>
--expected-sha256 <sha256> --expected-size <bytes>`; прямое повторное открытие
запрещено. Reader повторяет bounded `O_NOFOLLOW` identity validation и отдаёт
content только при exact match. `stdin` не превращать в repo artifact.

Прочитать report только из `stdin` или validated safe repo path. Каждый пункт
перепроверить против current code; authority автора не доказывает finding.
Статусы: `accepted`, `rejected`, `duplicate`, `needs-evidence`. Ни один пункт не
исправлять в этой фазе.

### `bug`

Передать symptom роли `bug-investigator`. Требовать цепочку
symptom → reproduction → call-chain → competing hypotheses → root-cause proof.
Без reproduction/evidence результат остаётся hypothesis/UNKNOWN; diagnostic
production edits запрещены.

### `security`

Запустить `python3 workflow/scripts/harness-security-audit.py [--json]`, затем
передать findings роли `security-reviewer` для contextual validation. Scanner
finding сам по себе не confirmed vulnerability. Недоступный/сломанный scanner
даёт `UNKNOWN`, а не PASS.

## Findings и routing

Каждый finding имеет: `DCR-N`, severity, confidence, status, exact path/range,
observation, evidence, violated contract/rule, impact и lifecycle route.

Если пользователь просит исправление после отчёта, вернуть только маршрут:

- contract/product change → `propose`;
- new/unmapped task или scope → `plan`;
- existing covered task → `implement`;
- iOS после fix → `verify`;
- Android после fix → terminal Verify unavailable; не писать `fixed` или
  `verified`.

Human-readable output писать на русском. Завершить scope, selected lenses,
findings/triage, unverified areas, lifecycle routes и statement `No edits made`.
Если post-check не `PASS`, вместо findings/verdict завершить `Review invalid:
repository mutation or incomplete guard coverage`; не писать `fixed`,
`verified` или `No edits made` и не скрывать safe changed path/categories.
