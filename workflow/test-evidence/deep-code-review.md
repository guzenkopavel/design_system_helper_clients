# Deep code review evidence

## RED baseline

До реализации проверка структуры зафиксировала:

```text
MISSING .agents/skills/deep-code-review/SKILL.md
MISSING workflow/phases/deep-code-review.md
MISSING workflow/roles/deep-code-reviewer.md
MISSING workflow/roles/bug-investigator.md
MISSING workflow/scripts/harness-security-audit.py
MISSING .claude/commands/deep-code-review.md
MISSING .opencode/commands/deep-code-review.md
MISSING iOS/workflow/phases/deep-code-review.md
MISSING Android/workflow/phases/deep-code-review.md
Harness lint: grade A (0 critical, 0 warnings)
```

## GREEN

- Portable skill и thin Claude/OpenCode commands ведут в один канон;
- Codex, Claude Code, Cursor и OpenCode имеют exact bindings трёх read-only
  ролей;
- iOS и Android используют отдельные addenda без смешивания platform lenses;
- invocation validator fail-closed проверяет mode, platform, package identity,
  Git ref, adapter `platform_root`, secret globs и bounded regular UTF-8 report;
- file report связывается с reviewer read через validated SHA-256/size и
  повторный bounded `O_NOFOLLOW` reader; replacement/mismatch не отдаёт content;
- machine guard сравнивает index и content snapshot tracked/staged/unstaged/
  untracked state через private ephemeral token и не пишет/revert repo;
- stdlib scanner покрывает runtime и canonical harness surfaces, поддерживает
  per-file/file-count/total budgets, redaction, `FAIL` exit `2` и incomplete
  coverage `UNKNOWN` exit `3`; `harness-lint` вызывает его без рекурсии.

Проверки:

```text
validate-deep-code-review self-test: PASS
read-deep-code-review-report self-test: PASS
deep-code-review-readonly-guard self-test: PASS
harness-security-audit self-test: PASS
Harness security audit: PASS (0 critical, 0 coverage issues)
harness-lint self-test: PASS (profiles + hooks + deep review security mutations)
Harness lint: grade A (0 critical, 0 warnings)
```

## Pressure scenarios

| Scenario | Expected result |
|---|---|
| `fix`, `--fix`, platform omission, traversal, unsafe report или ambiguous package | blocker до чтения/изменений |
| Production CLI `--root` override | unknown flag, exit `2` |
| `review ios --paths Android/...` или обратный direction | blocker по adapter `platform_root` |
| Report совпадает с adapter secret glob (`.mobileprovision`), directory/device | blocker до content read |
| Report oversized или invalid UTF-8 | bounded blocker без вывода content |
| Final symlink, growth или identity swap во время report read | blocker; не более budget + 1 byte |
| Report replacement/hash mismatch между validation и triage | identity-bound reader не отдаёт content |
| Same-context fallback | `Fresh-eyes independence: UNAVAILABLE`, не independent review |
| Feedback item без current-code proof | `needs-evidence` или `rejected`, без fix |
| Bug без reproduction/root proof | hypothesis/`UNKNOWN`, без diagnostic edits |
| Secret canary | critical finding; raw value отсутствует в JSON/human output |
| Broad permission/hook injection любого runtime | critical finding |
| Safe placeholder/security prose, включая `must reject Bash(*)` | finding отсутствует |
| Scanner stat/read/decode/oversize/budget/symlink escape | safe coverage issue, `UNKNOWN`, exit `3` |
| Scanner file growth/identity swap или candidate-set mutation | bounded coverage `UNKNOWN`, не PASS |
| Canonical phase или platform addendum canary | finding; omission canonical roots ломает self-test |
| Guard clean pre/post snapshot | `PASS`, private state удалён, repo state идентичен |
| Guard mutation already-dirty content при том же status | `INVALID`, exact safe path/category, без revert |
| Guard staged/index mutation или untracked add/change | `INVALID`, report запрещён, user state сохранён |
| Guard budget exhaustion/unsafe token | `UNKNOWN`/`INVALID`, valid report запрещён |
| Guard token symlink/replacement/oversize/wrong repo | bounded reject; valid token consumed on wrong-root check |
| iOS finding после отдельного fix | route в `verify ios` |
| Android finding после отдельного fix | route в `verify android`; review не `fixed/verified` до отдельного PASS |

Во всех modes `writes_artifacts: []` запрещает repository artifacts. Только при
guard `PASS` допустимы `No edits made` и lifecycle route. Guard
`INVALID|UNKNOWN` заменяет findings/verdict на `Review invalid` и запрещает
fixed/verified claims.
