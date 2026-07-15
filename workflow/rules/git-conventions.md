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
