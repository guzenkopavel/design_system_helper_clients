# Язык lifecycle-артефактов

Product и платформенный lifecycle хранят человекочитаемую authored-часть
артефактов и reports на русском языке. Правило действует для active product
package и current v1 platform package во всех validator modes.

Обязательные русскоязычные поверхности:

- authored prose в product `concept.md`, `brief.md`, `ux.md` и `spec.md`;
- authored JSON reports: product review `rationale`, finding `summary`/`evidence`,
  а также человекочитаемые current v1 platform meta impact/questions/problems; exact
  machine IDs, enums, paths и schema values освобождены;
- human tail в product `Approval evidence` и `UX artifact: NOT APPLICABLE`, а
  также retirement approval/disposition narrative; person names и exact paths
  остаются machine/name exemptions;

- authored prose в `proposal.md`, `implementation-spec.md`, `design.md`,
  `verification.md` и условном `platform-ux.md`;
- authored prose в `plan/README.md` и каждом `plan/task-NNN.md`;
- direct-child authored task reports `evidence/task-[0-9]{3}.md`;
- direct-child reconciliation reports по точному canonical contract
  `evidence/reconciliation-<YYYYMMDD>T<HHMMSS>Z-task-NNN[-<safe-slug>].md`.

На английском могут оставаться код, команды, repo-relative paths, filenames,
идентификаторы контрактов, названия SDK/framework/API, а также точные заголовки,
labels, enums и строки machine schema, требуемые валидатором. Это исключение не
разрешает писать по-английски объяснения, решения, требования, критерии,
архитектурные обоснования, шаги или результаты проверки.

Каждый самостоятельный содержательный prose block должен содержать осмысленный
русский текст, а его остаточная естественная речь после удаления machine tokens
должна быть преимущественно кириллической. Один русский абзац в начале или конце
файла не компенсирует англоязычные разделы. Англоязычный абзац внутри в остальном
русского документа также блокирует фазу.

Каждое самостоятельное английское natural-language предложение блокирует
артефакт независимо от общего соотношения букв: длинный русский текст не может
компенсировать английское предложение в том же абзаце.

Валидатор использует общий helper `workflow/scripts/artifact_language.py`,
проверяет только перечисленные authored surfaces, не выводит их
содержимое в ошибке и сообщает только repo-relative файл и bounded номера
блоков. Он не выполняет broad/rglob scan evidence. Произвольные verifier/runtime
`.md`, `.log`, screenshots, JSON, raw command logs, внешние и неизменяемые
evidence остаются raw output: они не требуют перевода и не могут служить русским
padding. Registry-anchored v0 освобождён от правила: исторические hash anchors
нельзя переписывать ради ретроактивной локализации. Ни Markdown, ни authored
meta JSON language checks не применяются к exact-hash v0 projection.
