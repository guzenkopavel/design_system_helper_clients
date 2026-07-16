---
phase: pre-commit-check
writes_artifacts: []
requires_verification: staged-index
recommended_roles: []
---

# Phase: Pre-commit Check

Запускать при явном `$pre-commit-check` и перед выполнением явной просьбы о
commit. После commit intent и до staging получить явный intended path set. Для
каждой platform/feature/change identity сначала завершить отдельный
`$reconcile-implementation`; не считать весь dirty worktree разрешённым scope.
Затем сверить requested ownership/scope с `git status`; сама фаза никогда не
выполняет `git add`.

Запустить `python3 workflow/scripts/pre-commit-check.py --staged`. Требовать
свежий staged fingerprint и точный общий `PASS`. Проверить разделение scope,
влияние на документацию и platform addenda. Для harness changes staged-index
checkout запускает `harness-lint --warn-as-error`. Для production paths
обязательны active task trail coverage и adapter obligations.

Gate остаётся read-only и не запускает reconciliation. Uncovered production
path даёт только actionable hint; автоматический repair или staging запрещены.

`FAIL`/`UNKNOWN` останавливает commit и сообщает paths/check identifiers без
значений секретов. После GREEN уже разрешённый commit можно продолжить без
повторного вопроса. Фаза не делает commit, push, hook installation или
destructive recovery.
