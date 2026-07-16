# Simple-model task evidence — RED → GREEN → REFACTOR

## Change plan

- **Тип / операция:** rule + phase + script + template · modify/add.
- **Зачем:** OpenCode-модель смешивала authored task result с raw path inventory,
  переписывала пути в fences и после выбора Android task анализировала foreign
  iOS lane из общего `git status`.
- **Scope:** `cross-platform`; контракт одинаков для iOS и Android.
- **Канонический владелец:**
  [`artifact-language.md`](../rules/artifact-language.md),
  [`implement.md`](../phases/implement.md) и
  [`artifact_language.py`](../scripts/artifact_language.py).
- **SSOT:** отдельная runtime/OpenCode policy не создана; adapters остаются thin.
- **Инварианты:** single writer; production/active packages/index immutable;
  русский authored result сохранён; reconciliation остаётся полностью authored;
  disjoint lanes не входят в selected task decision.

## RED

В приложенном пользователем trace `error.txt` OpenCode после выбора
Android `user-profile-auth/task-002` вернулся к общему состоянию репозитория и
пытался исправить iOS `task-001` evidence. Воспроизведён исходный helper на
direct-child task report:

```text
## Итог
Реализация добавляет проверенный контракт авторизации.

## Changed paths
iOS/.../AuthAPIClient.swift — API client contract
iOS/.../CheckEmailUseCase.swift — email availability use case
```

Результат до изменения: `exit 1`; diagnostic указывал failing authored blocks
для обеих raw path rows. Для прохождения требовались ручные code fences, хотя
строки являлись техническим inventory, а не решением или итогом.

## GREEN

Введён typed contract для exact direct-child `evidence/task-NNN.md`:

- ровно один содержательный русский `Итог`;
- canonical `Технические доказательства`, где только safe path/change rows и
  bounded exact repo-tooling commands не требуют fences; exact legacy
  `Changed paths` освобождает только safe path/change rows;
- остальные sections проходят прежний block/sentence language gate;
- reconciliation reports продолжают использовать полный authored gate.

Тот же report без fences проходит specialized validator. Implement теперь
следует deterministic route: selected task → exact context/profile → selected
lane snapshot; `INVALID` останавливает writes, `VALID` запрещает возвращаться к
общему `git status` и foreign evidence.

## REFACTOR pressures

`artifact_language.py --self-test` подтверждает:

1. English summary блокируется, включая compatibility heading `Summary`.
2. English prose в неизвестном authored section блокируется.
3. Canonical section принимает safe path/git/rename rows и bounded commands без
   fences; exact `Changed paths` принимает те же path/change rows, но блокирует
   standalone command/output.
4. Report только с raw section и report без summary блокируются.
5. Summary aliases ограничены exact набором; похожий неизвестный heading не
   получает exemption.
6. English `Tests were not run. Known limitation remains.` блокируется под
   обоими raw headings, прежними headings проверок/файлов, неизвестным heading и
   `Ограничения`.
7. Exact summary/raw names распознаются на H1 и H2: полностью русский H1 report
   проходит, English H1 summary и mixed H1/H2 duplicate summary блокируются;
   любой иной H1/H2 остаётся authored.
8. Path annotation принимает finite technical phrases `API client contract` и
   `email availability use case`, но блокирует no-punctuation English prose.
9. Command принимает `--feature user-profile-auth`, `--package-path iOS/Feature`
   и `--mode implement`, но не использует flag names для маскировки arbitrary
   bare English values (`--reason Tests --state were ...`).
10. Option names ограничены finite exact repo-tooling allowlist: exact repro
    `--tests-were-not-run-because-simulator-unavailable
    --known-limitations-remain-unresolved` блокируется; редкие flags требуют
    fenced command evidence.

Raw content является ненормативным technical inventory и не может заменять
outcome, решения или ограничения. Произвольный output требует fence либо
отдельного `.log`. Эвристический поиск слов `path`, `check` или `file` в
произвольном heading не вводился.

`validate-platform-change.py` отдельно маршрутизирует task reports в specialized
validator, а canonical reconciliation reports — в общий helper. Symlink,
package-boundary, regular-file и strict UTF-8 guards общие для обоих путей.

## Root documentation impact

- **README.md:** `update` — task-evidence rule не меняет capabilities, но во время
  работы current HEAD получил tracked source roots `Android/auth/` и
  `iOS/AuthFeature/`. Canonical render обновляет только generated capabilities
  row; manual prose не меняется.
- **workflow.md:** `update` — operational Implement route и task report contract
  стали проще и явно selected-lane.
- **deep-info.md:** `update` — добавлены validator routing, template ownership и
  generated inventory.

## Проверки

- `artifact_language.py --self-test`: `PASS`.
- `validate-implementation-scope.py --self-test`: `PASS`.
- Targeted canonical/legacy RED report без fences: specialized helper `PASS`;
  English output/outcome/limitation под обоими raw и любым non-raw heading:
  `FAIL`; command line в `Changed paths`: `FAIL`.
- Real current v1 Implement validation: iOS `VALID`; неизменённый Android H1
  `task-003` report принят и полный Android package также `VALID`.
- `validate-platform-change.py --self-test` и iOS legacy v0 check остановлены
  существующим отсутствующим production path Preview Assets в историческом
  `client-bootstrap`; изменение production запрещено scope этой работы.
- Android legacy v0 check и global harness lint остановлены параллельным
  user-owned изменением immutable `client-bootstrap/task-001.md`
  (`task_graph_sha256`); task/package не переписывались.
- Isolated current base `34fa689` + exact harness patch: canonical docs render,
  read-only check и harness lint фиксируются финальным verification run.
- `py_compile` и `git diff --check`: `PASS`.

Exact harness patch хранится отдельно от production commits и не включает
platform package/index state.

## Остаточные ограничения

Raw exemption намеренно line-level и ограничен direct-child task report:
safe path/change rows в двух exact H2, bounded commands только в canonical H2,
fenced verbatim и прежние exact machine rows. Он не делает broad heading/path
inference, не распространяется на nested Markdown и не позволяет English
authored output, outcome, decision или limitation.
