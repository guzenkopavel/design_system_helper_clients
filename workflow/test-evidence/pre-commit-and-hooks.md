# Pre-commit and hooks evidence

Scope: `cross-platform`. Канон общий; iOS и Android категории принадлежат
отдельным adapter profiles и проверяются независимо.

## RED snapshot

До изменения отсутствовали восемь обязательных частей:

1. portable skill `pre-commit-check`;
2. common phase с commit-intent boundary;
3. staged-index runner с fingerprint;
4. tracked executable `.githooks/pre-commit`;
5. единый runtime hook runner;
6. thin adapters для Codex, Claude Code, Cursor и OpenCode;
7. iOS/Android `pre_commit` profiles и platform addenda;
8. hook/pre-commit contracts, process wiring и regression evidence.

При этом прежний `harness-lint --warn-as-error` ошибочно возвращал grade `A`
с `0 critical / 0 warnings`: отсутствие механики не обнаруживалось.

## GREEN contract

- Gate читает staged index, а не unstaged worktree; fingerprint включает index
  metadata и binary diff и повторно проверяется перед verdict.
- `FAIL`/`UNKNOWN` блокируют commit; gate не stage/commit/push и не выдаёт
  delivery authorization.
- Harness changes проверяются staged `harness-lint`; production paths требуют
  active task coverage, а UI/localization/security — staged evidence.
- iOS и Android project/tool commands не зафиксированы: они выводятся только из
  обнаруженного проекта и task evidence.
- Runtime adapters передают payload общему runner; `--no-verify`, destructive
  Git и uncovered edits блокируются там, где runtime соблюдает exit semantics.
- Tracked Git hook всегда повторяет canonical gate и не устанавливается в
  `.git/` автоматически.
- Native common harness/spec edit payload не требует недоступного synthetic
  mode. Platform production/security/project edit использует active task и
  engineering scopes из repository state; pre-edit не требует result evidence.
- Claude и Cursor используют event-specific native post context; Codex post
  остаётся явно advisory/generic. OpenCode auto-load path —
  `.opencode/plugins/`, cwd — monorepo `worktree`; warning не теряется.

## Pressure matrix

| Scenario | Expected |
|---|---|
| unstaged secret при безопасном staged blob | `PASS`, значение не выводится |
| secret/key path или secret-like staged content | `FAIL` |
| index изменился после проверки | новый fingerprint / повторный gate |
| active feature spec placeholder | `FAIL`; root README/path examples/template/archive не затрагиваются |
| iOS production path без active task | `FAIL` |
| Android production path без active task | `FAIL` |
| один covered path и uncovered sibling | `FAIL` sibling |
| common harness/spec edit, native runtime payload | allow |
| iOS project/security edit с active task + engineering scopes | allow pre-edit |
| platform production edit без active task/scopes | runtime deny |
| Android local credential/keystore path | runtime deny |
| `rtk git`, absolute git, `command`/`env`, `git -C` destructive command | runtime deny |
| `/bin/sh -c`, `/bin/bash -lc`, nested shell с destructive Git | runtime deny |
| quoted prose `echo "git reset --hard"` | allow, без false positive |
| `git commit --no-verify` | deny без исключений |
| pending task или `Evidence: none` для production diff | blocking `UNKNOWN` |
| done task + concrete staged evidence | `PASS` при остальных GREEN checks |
| production deletion или обе стороны rename/copy без task | `FAIL` |
| malformed/missing staged platform adapter + platform path | `FAIL` closed |
| project config найден, но task command/result отсутствует | `UNKNOWN` |
| Cursor invalid event/failClosed/schema | harness lint finding |
| Claude/Cursor неправильная post warning schema | self-test/lint finding |
| OpenCode singular dir/directory cwd/before-after args/lost warning | harness lint finding |
| OpenCode invocation из repo root, `iOS/`, `Android/` | worktree-root PASS |
| activation `--install` при foreign hooks path | refusal, значение сохранено |

## Commands

Финальный snapshot записывается только после fresh запуска:

```text
python3 workflow/scripts/pre-commit-check.py --self-test
python3 workflow/hooks/hook-runner.py --self-test
python3 workflow/scripts/harness-lint.py --self-test
python3 workflow/scripts/harness-lint.py --warn-as-error
bash workflow/scripts/configure-git-hooks.sh --self-test
```
