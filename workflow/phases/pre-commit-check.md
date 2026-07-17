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
Commit может происходить до или после archive: до archive reconciliation и gate
используют active task trail, после archive — verified implementation archive
receipt/tombstone trail. Archived task coverage или verified scope coverage —
preferred evidence; валидный текущий verified archive также может покрывать
coherent post-archive delivery slice на package level.
Затем сверить requested ownership/scope с `git status`; сама фаза никогда не
выполняет `git add`.

Запустить `python3 workflow/scripts/pre-commit-check.py --staged --path <path>...`
с одним `--path` для каждого exact intended path. Для rename передать mutable
old/new; для copy — read-only unchanged source и mutable destination. Требовать
свежий staged fingerprint, точный общий `PASS` и созданный private short-lived
receipt. Проверить разделение scope,
влияние на документацию и platform addenda. Для harness changes staged-index
checkout запускает `harness-lint --warn-as-error`. Для production paths
обязательны active task trail coverage либо verified implementation archive
coverage. Для verified archive exact task/scope coverage preferred, но
package-level receipt coverage допускается с warning, если staged set несёт
текущий archive/tombstone trail и проходит adapter obligations. Для
post-archive verified receipt trail project/tool evidence берётся из terminal
archive receipt, а не требует повторного staged task command/result.

Gate остаётся read-only для repository/index/worktree, не запускает reconciliation;
единственная запись — private ephemeral receipt вне repo.
Uncovered production path даёт только actionable hint; автоматический repair
или staging запрещены.
Extra staged path, missing intended path, unsafe path или production boundary с
несколькими active package owners дают `FAIL`. Unrelated unstaged state
допустим, потому что Git commit включает index, а не worktree. Runtime hook
делает non-consuming receipt preview, tracked `--hook` атомарно потребляет
one-shot receipt и повторяет integrity. Generic hook без receipt не разрешает
commit; canonical coordinator проверка всегда выполняется с exact intended
binding.

`FAIL`/`UNKNOWN` останавливает commit и сообщает paths/check identifiers без
значений секретов. После GREEN уже разрешённый commit можно продолжить без
повторного вопроса. Фаза не делает commit, push, hook installation или
destructive recovery.
