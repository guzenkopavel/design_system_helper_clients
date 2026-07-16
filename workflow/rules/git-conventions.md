# Git conventions

Правило применяется только при явно согласованном delivery scope. Обычные
workflow-фазы не коммитят, не push-ят и не создают PR. Чужие staged/unstaged
изменения сохраняются.

## Безопасность

- Перед staging проверить status и отделить owned paths от пользовательских.
- Не использовать destructive reset, checkout, clean, force-push или history
  rewrite без отдельного явного разрешения.
- Не подмешивать unrelated изменения и generated noise.
- Один логический change — один reviewable commit, если пользователь запросил
  commit.

Commit subject — краткий imperative description наблюдаемого результата без
self-attribution. Формат языка и PR определяется правилами команды, обнаруженными
в репозитории; при их отсутствии это отдельное человеческое решение, а не
догадка агента.

Перед delivery повторить scoped verification, проверить diff, секреты,
конфликтные маркеры и отсутствие случайно staged файлов. Commit не является
доказательством проверки — evidence остаётся в lifecycle package.

После явного commit intent и завершённого scoped staging выполнить
`python3 workflow/scripts/pre-commit-check.py --staged --path <path>...`, передав
exact intended set: mutable old/new для rename, read-only unchanged source и
mutable destination для copy. `PASS` создаёт short-lived private
receipt для этого staged fingerprint; runtime preview его не потребляет, а
tracked hook забирает one-shot. `FAIL` и `UNKNOWN` останавливают commit.
`--no-verify` запрещён. Полный контракт:
[`pre-commit-integrity.md`](pre-commit-integrity.md).

Tracked hook можно активировать только явно и collision-safe. Сначала выполнить
`workflow/scripts/configure-git-hooks.sh --check`; только отдельный явный вызов
`--install` меняет local `core.hooksPath`, если значение пусто или уже равно
`.githooks`. Foreign hooks path скрипт отказывается перезаписывать. Автоматически
вызывать install или менять файлы внутри `.git/` нельзя.
