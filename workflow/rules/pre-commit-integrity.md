# Pre-commit integrity

Pre-commit — gate готовности уже разрешённого commit. Он не расширяет delivery
scope, не stage'ит файлы, не создаёт commit, не push'ит, не устанавливает hooks
и не исправляет failures разрушительными командами. После явной просьбы о
commit GREEN позволяет coordinator продолжить то же разрешение без повторного
подтверждения.

До staging explicit commit intent проходит каноническую последовательность:
явный intended path set → отдельный `reconcile-implementation` для каждой
platform/feature/change identity → reconciliation report → staging approved set
→ этот gate → commit.
Gate не вызывает reconciliation и не изменяет worktree/package; uncovered
production trail получает только actionable hint.

Ownership и `git status` проверяются до staging. Затем machine gate анализирует
staged index, а не worktree: entries, modes, blob content и binary diff образуют
один fingerprint. Изменение index инвалидирует результат; gate нужно повторить
непосредственно перед commit.

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
Каждый production path, включая deletion и обе стороны rename/copy, требует
completed active task и concrete evidence, staged вместе с изменением. Наличие
project config само по себе не даёт PASS: `tool_globs` обнаруживают tooling, а
task содержит discovered command и staged result evidence.

Missing/malformed platform contract закрывает gate для staged paths под
соответствующим platform root. Adapter читается из index, поэтому unstaged
worktree version не может подменить staged contract.

Связанные SSOT: [`git-conventions.md`](git-conventions.md),
[`orchestration-core.md`](orchestration-core.md),
[`test-execution.md`](test-execution.md) and
[`verification-evidence.md`](verification-evidence.md).

Tracked `.githooks/pre-commit` всегда повторяет canonical staged gate. Receipts
и advisory runtime reminders не являются доказательством. `--no-verify`
остаётся human Git bypass, и agents не должны его использовать.
