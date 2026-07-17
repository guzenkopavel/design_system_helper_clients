# Pre-commit integrity

Pre-commit — gate готовности уже разрешённого commit. Он не расширяет delivery
scope, не stage'ит файлы, не создаёт commit, не push'ит, не устанавливает hooks
и не исправляет failures разрушительными командами. После явной просьбы о
commit GREEN позволяет coordinator продолжить то же разрешение без повторного
подтверждения.

До staging explicit commit intent проходит каноническую последовательность:
явный intended path set → отдельный `reconcile-implementation` для каждой
platform/feature/change identity → reconciliation report → staging approved set
→ этот gate → commit. Эта последовательность не зависит от lifecycle момента:
до archive она опирается на active task trail, после archive — на tombstone и
verified implementation archive receipt trail, включая immutable archived task
coverage или verified scope coverage.
Gate не вызывает reconciliation и не изменяет worktree/package; uncovered
production trail получает только actionable hint.

Ownership и `git status` проверяются до staging. Затем machine gate анализирует
staged index, а не worktree: entries, modes, blob content и binary diff образуют
один fingerprint. Exact `PASS` canonical invocation с `--path` создаёт вне
репозитория короткоживущий receipt: private directory `0700`, regular file
`0600`, repository/Git-dir identity, staged fingerprint и exact intended paths.
Receipt не расширяет пользовательскую авторизацию и не является repository
artifact. JSON читается strict: `NaN`, `Infinity`, `-Infinity`, boolean/non-finite
timestamps, неверный порядок или TTL блокируются.

Каноническая delivery invocation передаёт exact intended set повторяемыми
`--path`. Safe repo-relative set должен точно совпасть со всеми staged paths;
rename identity включает mutable old/new, copy identity — read-only unchanged
source и mutable destination. Обе стороны обязательны в intended/receipt;
missing intended или extra
foreign staged path дают `FAIL`, потому что commit включает весь index.
Unrelated unstaged state разрешён. Если один production path покрывают tasks из
нескольких active packages или verified archives, owner считается ambiguous и
gate блокирует delivery; несколько последовательных tasks одного package
сохраняют DAG semantics.

Gate проверяет staged ownership/scope, whitespace и conflict markers,
подозрительные generated/local files, debug/investigation markers, secret-like
paths/content без печати значений, placeholders в active specifications,
platform production task coverage и harness integrity. Один корректный path не
скрывает uncovered или unsafe sibling.

Shared product placeholder check применяется только к feature package artifacts
`concept.md`, `brief.md`, `ux.md`, `spec.md`. `specs/product/README.md`, path
examples, templates и archive не считаются active specification.

Platform build/test/UI/localization/security obligations приходят из adapter
`pre_commit`. Отсутствующие tools или runtime evidence дают `N/A` либо
`UNKNOWN` по риску; `UNKNOWN` никогда не считается PASS. Commands, projects,
schemes, targets, variants и destinations обнаруживаются, а не выдумываются.
Каждый mutable production path, включая deletion, rename old/new и copy
destination, требует либо completed active task with staged evidence, либо
completed archived task/verified scope inside a verified implementation archive
receipt. Implementation-retirement receipts do not satisfy delivery coverage.
Copy source не требует task write ownership/evidence, но обязан быть explicit,
byte-equal, unchanged, safe, no-symlink и принадлежать тому же adapter; его
regular stage-0 mode/blob в index и worktree обязаны точно совпадать с HEAD,
без cached/unstaged delta или unmerged entries. Он также называется в
reconciliation evidence. Наличие
project config само по себе не даёт PASS: `tool_globs` обнаруживают tooling, а
task содержит discovered command и staged result evidence.

Missing/malformed platform contract закрывает gate для staged paths под
соответствующим platform root. Adapter читается из index, поэтому unstaged
worktree version не может подменить staged contract.

Связанные SSOT: [`git-conventions.md`](git-conventions.md),
[`orchestration-core.md`](orchestration-core.md),
[`test-execution.md`](test-execution.md) and
[`verification-evidence.md`](verification-evidence.md).

Runtime hook перед `git commit` выполняет non-consuming preview: требует свежий
receipt и повторяет staged integrity, но не забирает receipt. Tracked
`.githooks/pre-commit` запускает `--hook`, атомарно потребляет receipt ровно один
раз как one-shot и снова проверяет staged index. Absent, expired, malformed, symlink,
wrong-mode, wrong-repository, stale fingerprint, path mismatch и replay дают
`FAIL`. Generic integrity без receipt не авторизует commit; coordinator exact
gate остаётся обязательным. `--no-verify` остаётся human Git bypass, и agents не
должны его использовать.
