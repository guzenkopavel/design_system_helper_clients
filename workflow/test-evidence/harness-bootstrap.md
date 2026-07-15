# Harness bootstrap — test evidence

## Scope

Проверены [`harness-change`](../../.agents/skills/harness-change/SKILL.md),
[`harness-review`](../../.agents/skills/harness-review/SKILL.md), связанный
[`writing-skills`](../../.agents/skills/writing-skills/SKILL.md) и
[`harness-lint.py`](../scripts/harness-lint.py).

## RED

Временный skill `harness-probe` содержал одновременно:

- несовпадение `name` и имени каталога;
- битую ссылку на каноническую phase;
- отсутствующую каноническую phase.

Команда `python3 workflow/scripts/harness-lint.py --json` завершилась с кодом 2
и результатом `grade D`: 2 critical, 1 warning.

## GREEN

После удаления probe та же команда завершилась с кодом 0 и результатом
`grade A`: 0 critical, 0 warnings.

`quick_validate.py` из skill-creator отдельно подтвердил `Skill is valid!` для
всех трёх skill-каталогов.

## REFACTOR

Линтер проверяет независимые классы ошибок: links, skill metadata/canonical,
agent TOML/dispatch, platform contract и naming. JSON и human-readable режимы
используют один набор findings и одну grade-функцию.

## Multi-runtime parity

Добавлен временный канонический fixture с именем `runtime-probe` без runtime bindings.
Линтер завершился с кодом 2 и результатом `grade F`: по одному critical для
Codex, Claude Code, Cursor и OpenCode. После удаления probe линтер вернулся к
`grade A`.

Проверки обнаружения:

- `opencode debug skill` обнаружил `harness-change`, `harness-review` и
  `writing-skills` из `.agents/skills/`;
- `opencode debug agent <name>` разрешил обе project-роли и их permissions;
- resolved OpenCode command registry содержит три одноимённых slash-команды;
- `claude agents` обнаружил `harness-auditor` и `implementation-writer`;
- Claude Code использует thin slash-команды из `.claude/commands/`, а portable
  skill SSOT остаётся только в `.agents/skills/`;
- Cursor adapter проверен статически, поскольку Cursor CLI отсутствует в
  текущем окружении.
