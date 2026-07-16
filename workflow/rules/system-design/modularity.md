# Cross-platform modularity

Этот platform-neutral контракт задаёт strong default для physical boundaries.
Граница следует cohesive capability/ownership и реальному consumer/dependency
graph, а не названиям папок или горизонтальных layers. Папка сама по себе не
является module/package/target.

## Strong default (v1)

Новая независимая feature, domain data capability с repository/data sources,
transport/networking, persistence/storage и reusable UI/design-system
capability по умолчанию изолируется в platform-native physical unit с
минимальным public contract. Конкретный вид unit определяет adapter по
обнаруженному project/build graph.

Application shell разрешено владеть только exact allowlist:
`entry-points, lifecycle, root-routing, dependency-wiring,
platform-configuration, target-resources`. Его capability ownership всегда
`none`: shell только компонует реализации; feature/domain/data/network/
persistence/reusable-UI implementation и mutable state в нём запрещены.

Dependency graph ацикличен. Consumers зависят от contracts, не implementation
details. Transport не владеет domain semantics. Data capability скрывает
sources за repository/contracts; feature не обращается к sources напрямую.

## Обязательное решение

`design.md` фиксирует один outcome: `isolated`, `deviation` или
`not-applicable`.

Machine-readable input решения имеет exact форму:
`independent-feature=yes|no; domain-data=yes|no; network=yes|no;
persistence=yes|no; reusable-ui=yes|no; consumers=<integer>;
independent-ownership=yes|no`. `Repository evidence` — разделённый `;` список
существующих безопасных repo-relative file/directory paths, а не narrative или
будущий путь.
Две exact строки `App-shell responsibilities` и
`App-shell capability ownership` — единственные допустимые утверждения об
application shell. Остальные free-form поля не могут содержать ни один из
токенов `app`, `application`, `shell`, `target`, `module` независимо от порядка,
possessive формы или ownership verb. В `Physical boundaries` разрешены только
adapter-approved non-application unit phrases; произвольный application
target/module невалиден. Дополнительный prose
в structured section запрещён.

- `isolated` требует adapter isolation scope, перечисленных physical units,
  public contracts, dependency direction, consumer integration и composition-
  only app shell;
- `deviation` допустим только внутри существующего/обнаруженного
  platform-native non-application physical unit, с точным repository constraint
  evidence, rationale/trade-offs, typed contract seam уже сейчас, migration
  boundary и объективным trigger. Application shell не может быть unit
  deviation; «быстрее», «маленький репозиторий» и существующий monolith сами по
  себе не являются основанием;
- `not-applicable` требует evidence, что поведение маленькое, cohesive и имеет
  не более одного consumer, все capability triggers равны `no`, independent
  ownership отсутствует, а physical split не улучшает ownership, testability,
  visibility или reuse.

Не создавать module на каждую папку, class или layer. Маленькое локальное
поведение остаётся cohesive, если split даёт только build/API overhead. Отдельный
API/implementation unit нужен лишь при evidence нескольких implementations,
consumers, независимого ownership/testability или visibility boundary.

## Lifecycle obligations (v1)

- Propose обнаруживает layout/consumers, записывает structured modularity
  decision и получает `PASS` boundary guard; missing/`BLOCK` verdict запрещает
  `design_gate: PASS`.
- Plan материализует unit manifest/project wiring, minimal public API, contract
  tests, consumer integration/build, dependency graph и app-shell composition;
  каждая task называет boundary owner.
- Implement не переносит feature/data/network implementation или mutable state
  в app shell и не расширяет sealed deviation.
- Verify проверяет realized graph, visibility/public API, module-level tests,
  consumer build и app-shell allowlist. Недоступные graph/tooling дают
  `UNKNOWN`, не `PASS`.

Platform mechanics принадлежат platform addenda; этот файл не задаёт SDK,
build tool, названия units, paths или commands.

## Contract version

Новые packages создаются только с `modularity_contract_version: 1`; adapter
объявляет тот же `modularity.contract_version`. Отсутствующее поле означает v0
только для `planned|implementing|verified` identity, зарегистрированной в
[`modularity-v0.json`](../../compatibility/modularity-v0.json), с полностью
совпавшей immutable historical structure.

Registry хранит exact platform/feature/change/package path и SHA-256 полного
`design.md`, immutable meta identity projection, полного
`plan/rule-selection.json`, полного `plan/README.md` и sorted task graph.
Нормализация task graph игнорирует только значения exact полей `Status` и
`Evidence`; filenames, paths, scopes, dependencies, inline contracts, commands
и остальной task content неизменяемы.
Legacy meta использует exact historical key set: immutable projection включает
все поля, кроме `status`, `tasks_done`, `problems`, `verification_status`,
`verified_at`, `verification_state`. Поэтому `blocking_questions`,
`tasks_total` и любое extra поле не могут измениться.

Canonical SHA-256 всего registry и ordered list ровно двух historical
identities/paths дополнительно pinned в common resolver code. Registry-only
append/edit, даже с корректно пересчитанными package hashes, не создаёт новый
trusted v0. Изменение anchor требует совместного code+registry harness change и
fresh audit.

Anchored v0 package может завершить Implement/Verify/Archive только по
историческим task paths и adapter `legacy_task_checks`. Его не оценивают
ретроактивно по v1 composition/app-shell rule, но он не может расширять
ownership, design, scopes, plan или task semantics. Любой mismatch или
незарегистрированная identity маршрутизируется в отдельный migration/new change
package. Неизвестная версия всегда блокируется.
