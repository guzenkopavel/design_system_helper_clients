# Repository documentation

Root documentation состоит ровно из трёх файлов с разной глубиной:

- `README.md` — короткий обзор проекта, корней, capabilities и entrypoints;
- `workflow.md` — практический operational guide от идеи до commit gate;
- `deep-info.md` — полный wiring, ownership, schema и file inventory reference.

Имена case-sensitive. Варианты `Readme.md`, `Workflow.md`, `deepInfo.md` и иные
синонимы запрещены: они создают неоднозначную поверхность для людей и runtime.

## SSOT boundary

Root docs объясняют и проецируют систему, но не владеют lifecycle policy.
Каноническое знание остаётся в `workflow/`, platform contracts/addenda/rules/
roles и `process/`. Если prose root-документа расходится с каноном, исправить
prose и не менять канон только ради совпадения документации.

Не копировать полные procedures, rule corpora, platform profiles или transient
package instances. Разрешены короткие маршруты, примеры invocation, schema и
ссылки на владельца.

## Documentation impact matrix

Каждый `harness-change` обязан указать для каждого root-документа disposition
`update` или `no-impact` с отдельным rationale.

| Изменение | README.md | workflow.md | deep-info.md |
|---|---|---|---|
| project root, client capability, top-level entrypoint | update | проверить маршрут | update/generated |
| skill, phase, invocation или artifact contract | проверить обзор | update | update/generated |
| rule, role, script, template, hook, runtime binding | обычно no-impact | проверить operational effect | update/generated |
| platform contract/addendum/rule/role | update при capability/root change | проверить platform claim | update/generated |
| typo без semantic/structure impact | no-impact | no-impact | no-impact |

`no-impact` без rationale не принимается. Structural render не доказывает
semantic `no-impact`: writer обязан перечитать соответствующую audience layer.

## Generated и manual boundaries

Только exact blocks между `BEGIN GENERATED` и `END GENERATED` принадлежат
[`harness-docs.py`](../scripts/harness-docs.py). `render` может менять только
эти блоки и обязан сохранять manual prose byte-for-byte. Generated block нельзя
редактировать вручную; изменить canonical source и повторить render.

Manual prose владеет объяснением, примерами, decision tree, ownership и
ограничениями. Оно обновляется осознанно и проверяется semantic audit.

## Freshness

Structural freshness проверяет:

- exact filenames и корректные unique markers;
- skill↔phase, adapter capability/profile и platform addendum graph;
- runtime command/role/hook parity;
- deterministic harness inventory и repo-relative local links;
- валидные JSON/frontmatter и отсутствие локальных absolute/source paths.

Inventory включает common/platform harness, portable skills, runtime bindings,
process map, hooks и notices, включая untracked harness files текущего change.
Он исключает native source/build output, caches, transient specs/packages и тела
лицензий.

Semantic freshness проверяет:

- корректность capabilities, invocation и write/evidence claims;
- разделение аудиторий без противоречий и лишнего дублирования;
- SSOT ownership и platform isolation;
- отдельную точность iOS и Android утверждений.

Порядок завершения wiring cascade:

```text
python3 workflow/scripts/harness-docs.py render
python3 workflow/scripts/harness-docs.py check --json
python3 workflow/scripts/harness-lint.py --json
```

`check` read-only и fail-closed. `harness-lint` вызывает тот же checker без
рекурсии. Grade A не заменяет semantic verdict `CLEAN` от `harness-review`.
