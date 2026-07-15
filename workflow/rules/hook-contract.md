# Hook contract

`workflow/hooks/hook-runner.py` — общая реализация. Runtime JSON/TS files только
нормализуют payload и вызывают её с runtime/event; policy в них не копируется.

Pre-tool guards запрещают dangerous Git и запись secret/key paths. Вызов commit
запускает staged pre-commit gate. Common harness/spec edits проходят с native
runtime payload без синтетического mode. Platform production edits требуют
active task coverage; project/security surfaces дополнительно требуют
engineering scopes из task. Pre-edit не требует post-edit evidence. Post-edit
checks дают только warning для active placeholders и mobile security surfaces,
чтобы не блокировать cleanup.

Exit `0` разрешает операцию, exit `2` запрещает её, если runtime соблюдает
command exit status. Tracked Git hook остаётся enforcement backstop. Runtime
surfaces с advisory-only hooks нельзя описывать как hard blocker.

Git parser распознаёт прямой/absolute `git`, `git -C`, `rtk`, `command`, `env`,
а также рекурсивно проверяет bounded `sh|bash -c|-lc`; eval не используется,
quoted prose не интерпретируется как команда.

Runtime output зависит от event: Claude `PostToolUse` получает
`hookSpecificOutput.additionalContext`, а deny `PreToolUse` — native
permission decision и blocking exit. Cursor pre-tool получает
`permission: allow|deny`, post-tool — `additional_context`. Для Codex post-tool
остаётся generic/advisory: подтверждённый native context contract не заявляется.
OpenCode plugin загружается из `.opencode/plugins/`, запускает runner с `cwd`
равным monorepo `worktree` даже при client directory `iOS/` или `Android/`,
передаёт before `output.args`, after `input.args` и показывает `warn` через
stderr console.
