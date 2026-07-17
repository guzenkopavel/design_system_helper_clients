# Task Evidence — task-NNN

<!-- Authored prose по-русски. Exact commands, paths, IDs, statuses и code/API
names не переводить. Raw tool output хранить в fenced block или отдельном
bounded `.log`; не вставлять произвольный stdout как обычный prose. -->

## Итог

Коротко зафиксировать выполненный task outcome, какие declared Paths изменены и
какое focused evidence подтверждает готовность task.

## Технические доказательства

Допустимые unfenced строки:

- safe path/change rows: `path | change | evidence`;
- bounded repo-tooling command lines: `rtk ...`;
- git status rows только для selected lane, если они нужны для доказательства
  scope; общий `git status` и foreign/disjoint lane не переносить.

Произвольный raw output:

```text
Поместить сюда только bounded output, необходимый для task evidence, либо
сослаться на отдельный `.log`.
```

## Проверки

- Focused checks: `<command or evidence path>` — `<PASS|FAIL|UNKNOWN>`.
- Scope check: `<command or evidence path>` — `<PASS|FAIL|UNKNOWN>`.

## Остаточные риски

Зафиксировать только риски, оставшиеся внутри scope задачи. Не использовать
этот раздел для новых требований или расширения task Paths.
