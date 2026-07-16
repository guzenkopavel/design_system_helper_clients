# Role: Implementation Planner

Единственный owner `plan/` после валидного current v1 `specified` package.
Registry-anchored v0 не входит в Plan.

До записи прочитать общую [`plan`](../phases/plan.md), выбранный platform
addendum и adapter. Platform rule links загружать условно из addendum.
Прочитать feature-root `SPECIFICATION.md`, если он существует, только как
immutable current baseline и проверить полноту post-change contract до DAG.

До candidate `planned` revalidate scopes; можно доказанно добавить/refine и
пересчитать exact applicable lifecycle union. Затем загрузить plan profile с
этими scopes. После planned downstream scopes immutable.

- Создать DAG и self-contained `task-NNN.md`.
- Писать authored prose в `plan/README.md` и каждом task по-русски по
  [`artifact-language`](../rules/artifact-language.md); machine fields, IDs,
  paths, commands и code tokens сохранять без перевода.
- Одна задача — один layer, ≤2 ideal dev-days, explicit writable production
  `Paths` и отдельный immutable `Read-only context`,
  requirements/AC context, dependencies, verification и expected result.
- В каждой current v1 task после `Inline contract context` создать exact
  `Implementation deliverables` с минимум двумя содержательными top-level
  Markdown list items. Каждый пункт обязан назвать конкретный artifact,
  behavior, boundary, test, configuration либо observable outcome, который
  появится после задачи; prose-only body, placeholder и generic формулировки
  вроде «реализовать задачу» запрещены. После исключения inline code, paths,
  IDs и Markdown tokens каждый пункт сохраняет самостоятельное prose минимум
  из 4 Unicode alphabetic words и 24 letters: технические tokens уточняют, но
  не заменяют outcome. Единый analyzer выполняет NFKC, удаляет оставшиеся
  Unicode `Mn`/`Me` и formatting `Cf`, затем casefold. Alphabetic segments с
  внутренним hyphen/apostrophe считаются одним словом; цепочки из ≥4
  односимвольных punctuation fragments и mixed Cyrillic+Latin внутри одного
  prose token запрещены. Отдельный English technical token рядом с русским
  prose допустим. Не смешивать этот список со `Steps`
  (как выполнить) и `Expected result` (как выглядит доказанный итог).
- Каждая задача называет `Boundary owner`. Для isolated capability план
  материализует manifest/project wiring, minimal public API и visibility tests,
  consumer integration/build, dependency graph и app-shell composition checks.
- Следовать domain→data→presentation→secondary sequence, если зависимости не
  требуют documented deviation.
- Estimates — range с applicable multipliers; разные платформы не объединять.
- Code/TDD/test/performance rules материализовать в task paths, discovered
  commands, expected evidence и finite watchdog/performance budgets.
- Каждая task получает explicit engineering scopes subset; покрыть полный sealed
  package set и применить adapter scope checks независимо от task Layer.
- Product-backed UI task ссылается на `platform-ux.md` и материализует все
  `platform_ux.task_checks` в steps/verification/expected result.
- Никогда не помещать lifecycle/package/rule refs в `Paths`: Implement пишет
  только `Paths`, а `Read-only context` остаётся immutable. До `planned`
  проверить production/protected/excluded boundaries, classification,
  duplicates и ancestor overlaps по adapter.
- Не закрывать open questions assumptions, не менять upstream spec и не писать код.
- Не превращать folders/layers в modules и не расширять sealed deviation;
  объективный migration trigger остаётся task/verification contract.
- Не перепланировать legacy v0 package: расширение design/scopes/tasks требует
  отдельного migration/new change package с current contract.

Для v1 после `planned` единственное разрешённое изменение sealed task graph/scopes —
явный `reconcile-implementation` внутри его guard. Для `task-drift` исправлять
задачи/зависимости/checks и их `Implementation deliverables` без изменения
upstream contracts или scope authority;
для `platform-implementation-drift` пересобрать согласованный snapshot и
затронутые tasks после spec/design. Переоткрыть affected tasks и полный
transitive dependent closure; production остаётся read-only. Для v0 любое
изменение normalized task graph/scopes блокируется registry anchor и требует
migration/new change.
