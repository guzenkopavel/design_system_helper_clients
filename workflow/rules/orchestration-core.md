# Orchestration core

## Single-writer

В рамках одного harness-change изменять файлы должен один writer. Аудитор и
другие review-роли работают read-only. Это сохраняет единый diff и исключает
конфликтующие правки.

## Bounded fix-loop

После проверки передавать writer только подтверждённый fix-list, затем повторять
проверку. После трёх итераций с одной и той же блокирующей причиной остановиться
и запросить решение пользователя.

## No-commit

Не выполнять `git commit`, `git push` и создание pull request без явной просьбы
пользователя.

Успешный pre-commit gate подтверждает готовность конкретного staged fingerprint,
но не создаёт и не продлевает delivery authorization. Любое изменение index
после gate требует повторной проверки в рамках той же явной просьбы.

## Independent work lanes

Lane — это явная identity, набор mutable path boundaries и immutable read
dependencies. Platform lane идентифицируется как `platform + feature +
change_id`; task дополнительно сужает mutable boundary до собственных `Paths`.
Product lane идентифицируется feature, delivery lane — точным intended staged
set. Read/read пересечение допустимо. Write/write и write/read пересечения
конфликтуют; общие harness/control-plane authorities всегда считаются общей
зависимостью и не могут изменяться параллельно с lifecycle lane.

Implement, Verify и Reconcile сравнивают только scoped projection выбранной
lane: selected package, task/realized production Paths, `Read-only context`,
shared product spec, `applicable_rule_files`, adapter и common/platform control
plane. Dirty/index/HEAD изменения вне этой projection не инвалидируют lane.
Изменение выбранной mutable/immutable projection или её index по-прежнему
блокирует guard. Persistent locks не создаются; race с archive остаётся
fail-closed residual risk существующих archive/identity gates.

Несколько active packages допустимы при явном `--change`. Omitted identity
разрешена только при одном classified active package и отсутствии partial/
unclassified siblings. Production boundary не может принадлежать нескольким
active packages: ambiguity блокирует Implement baseline, Reconcile и
pre-commit preflight, но последовательное пересечение tasks одного package
сохраняет обычную DAG semantics.

Каждый direct child active changes namespace классифицируется fail-closed:
regular active package с `meta.json`, exact tombstone-only directory либо
partial/unclassified sibling. Явный `--change` изолирует корректный package и
допускает foreign junk sibling; omission при таком sibling блокируется.
Writable production paths во всех platform phases проходят один canonical
lexical/canonical ownership helper. Existing file, directory boundary и
proposed child не могут пересекать protected roots или проходить через symlink.
Delivery change-entry helper отдельно фиксирует identity и write authority:
rename old/new входят в mutable set; copy source+destination входят в identity,
но source остаётся unchanged read-only, а mutable/task-covered только destination.
Explicit source выбирается из intended, identical repository candidates не
добавляются автоматически. Read-only source имеет ровно одну regular stage-0
index entry; index mode/blob и worktree mode/blob совпадают с HEAD, staged,
unstaged, deletion и unmerged delta запрещены.
