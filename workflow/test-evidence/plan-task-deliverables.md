# Plan task deliverables — RED/GREEN

## Change plan

- **Тип:** rule + phase + skill + role + script + template + process map.
- **Операция:** modify.
- **Зачем:** task plan должна отдельно и списком отвечать, что появится после
  реализации; `Steps` не заменяет этот контракт.
- **Scope:** cross-platform.
- **Канонический владелец:** `workflow/phases/plan.md` и
  `workflow/templates/platform-plan-task.md`.
- **SSOT-проверка:** отдельного deliverables-контракта не было; существующие
  `Steps` и `Expected result` имеют другие назначения и сохранены.
- **Инварианты:** current modularity v1 only; registry-anchored v0 и archives не
  изменяются; single writer; без production/spec/archive writes; без commit.

## RED

До изменения выполнено:

```text
python3 workflow/scripts/validate-platform-change.py --self-test
```

Результат: `PASS`. Current-v1 synthetic задачи для реальных iOS и Android
adapter содержали substantive `Steps`, но не содержали `Implementation
deliverables`. Значит прежний gate не доказывал наличие отдельного списка того,
что будет реализовано.

## GREEN

Для current v1 добавлен exact section `## Implementation deliverables` между
`Inline contract context` и `Steps`. Machine gate требует минимум два
содержательных top-level Markdown list item. Dedicated line parser считает H2 и
items только в column zero вне fenced code и blockquote, сохраняя исходную
indentation; literal heading внутри code не создаёт section/duplicate.
Placeholder и generic action envelope отклоняются после удаления inline-code,
path и ID padding. Это deny-list очевидно неспецифичных формулировок, а не
закрытый positive-словарь терминов. До generic check stripped prose обязано
содержать минимум 4 Unicode alphabetic words и 24 letters. Поэтому code/path/ID
могут уточнять пункт, но не заменяют independent prose. Этот floor доказывает
минимальную языковую содержательность, а не полную инженерную конкретность;
последняя остаётся обязанностью implementation-planner и harness review.

Floor и generic deny используют один поток: NFKC сохраняет precomposed буквы
вроде `й`, оставшиеся categories `Mn`/`Me` и formatting `Cf` удаляются, затем
выполняется casefold. Linguistic tokenizer считает alphabetic segments с
внутренним hyphen/apostrophe одним словом. Цепочка из ≥4 односимвольных
punctuation fragments и mixed Cyrillic+Latin scripts внутри одного prose token
блокируются. Отдельный English technical token не смешивается с соседним
русским prose и допустим.

## Pressure scenarios

| Сценарий | Ожидание | Результат |
|---|---|---|
| Нет exact section | FAIL | PASS |
| Section повторён либо расположен не между context и Steps | FAIL | PASS |
| Весь fake section находится в fence или blockquote | FAIL | PASS |
| Валидный section содержит literal fenced heading | PASS без duplicate | PASS |
| Section содержит только prose | FAIL | PASS |
| Nested пункт и только один реальный top-level пункт | FAIL | PASS |
| Два substantive пункта | PASS | PASS |
| Bullet + numbered item с конкретными русскими behavior outcomes | PASS | PASS |
| «Реализовать необходимую задачу» + «Выполнить требуемую работу» | FAIL | PASS |
| «Создать необходимые изменения в проекте» + «Добавить нужные проверки результата» | FAIL | PASS |
| Два `path — production файл` | FAIL independent prose floor | PASS |
| Два `` `CodeType` — Swift тип для REQ/AC `` | FAIL independent prose floor | PASS |
| Два `REQ/AC — product контракт и результат` | FAIL generic envelope | PASS |
| Два произвольных unknown-jargon пункта из 2–3 слов | FAIL independent prose floor | PASS |
| Два длинных generic action envelope | FAIL generic envelope | PASS |
| Hyphen и dot/slash chains из ≥4 односимвольных fragments | FAIL fragmentation | PASS |
| Combining accent в `необхо́димые` | Нормализуется и остаётся generic FAIL | PASS |
| Mixed lookalikes `всe нeобходимыe` | FAIL mixed Cyrillic/Latin token | PASS |
| Zero-width `Cf` внутри generic слова | Удаляется и остаётся generic FAIL | PASS |
| NFKC сохраняет `файлы`/`настройки`; long variants generic | FAIL generic envelope | PASS |
| Обычное русское hyphenated word | PASS как один token | PASS |
| Отдельный English technical term в русском outcome | PASS | PASS |
| Placeholder в пункте | FAIL | PASS |
| Deliverables есть, но `Steps` пуст | FAIL | PASS |
| Пункты находятся только в fenced code или nested list | FAIL как список | PASS |
| Одинаковый current-v1 fixture через iOS и Android adapters | PASS | PASS |
| Реальные registry-anchored v0 iOS и Android packages | VALID без retrofit | PASS |

## Wiring

- Plan phase, portable skill и implementation-planner создают новый раздел.
- Implementation writer читает полный список до writes.
- Reconciliation сохраняет его при `aligned` и согласованно ремонтирует только
  в разрешённом drift class.
- Process map и operational root documentation объясняют различие между
  deliverables, Steps и Expected result.

## Root documentation impact

- **README.md:** `no-impact` — project roots, capabilities и top-level
  entrypoints не изменились.
- **workflow.md:** `update` — operational task schema получила отдельный
  deliverables-контракт.
- **deep-info.md:** `update/generated` — reference schema и harness inventory
  должны отражать новый task contract и этот evidence.

## Остаточное ограничение

Machine gate доказывает структуру, independent prose floor и отклонение
описанных generic envelopes, но не может доказать инженерную конкретность
произвольного естественного языка. Это остаётся явной обязанностью planner и
semantic harness review.
