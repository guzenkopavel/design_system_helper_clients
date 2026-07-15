# Developer experience

DX scope охватывает путь от checkout до воспроизводимого build/test и понятной
диагностики. Он условный: продуктовая задача не должна автоматически менять
tooling, dependencies или onboarding.

## Review lens

- Зафиксировать baseline: команда, длительность, failure mode, output noise,
  cache state и число setup steps.
- Предпочитать быстрый targeted feedback широкому прогону без причины.
- Документировать только реально найденные prerequisites, environment values и
  команды; неизвестное отмечать явно.
- Dependency change проверять на lockfile consistency, совместимость, security,
  license, size и rollback.
- CLI/scripts должны иметь стабильные arguments, exit codes, non-interactive
  режим, понятные ошибки и cleanup дочерних процессов.
- Refactor tooling сохраняет behavior и отделяется от продуктового изменения.
- Generated artifacts имеют канонический source и воспроизводимую команду.

DX-задача считается проверенной не по субъективному «стало удобнее», а по
сравнимой метрике или воспроизводимому сокращению setup/failure path. Она не
разрешает commit, branch, package update или внешнюю публикацию без отдельного
delivery authorization.
