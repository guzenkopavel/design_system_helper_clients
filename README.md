# Mobile clients

Монорепозиторий двух нативных клиентов помощника-тренажёра для технических
собеседований разработчиков по проектированию и реализации дизайн-систем. iOS
и Android реализуются независимо, но используют общий продуктовый контракт и
один lifecycle харнеса.

Если вы впервые открыли репозиторий:

- [`workflow.md`](workflow.md) — практический маршрут от идеи до архива;
- [`deep-info.md`](deep-info.md) — полная карта wiring, файлов и ownership;
- [`AGENTS.md`](AGENTS.md) — обязательные правила для агентной работы.

## Проекты и спецификации

- [`iOS/`](iOS/) и [`Android/`](Android/) — самостоятельные native clients;
- [`specs/product/`](specs/product/) — общий product SSOT для обоих клиентов;
- [`iOS/specs/`](iOS/specs/) и [`Android/specs/`](Android/specs/) — отдельные
  implementation packages и evidence каждой платформы.

<!-- BEGIN GENERATED: README_CAPABILITIES -->
| Клиент | Source/build roots | Platform specs | Capabilities | Addenda | Rules |
|---|---|---|---|---:|---:|
| iOS | [`iOS/SysDevScen/`](iOS/SysDevScen/) | [`iOS/specs/`](iOS/specs/) | `propose` → `plan` → `implement` → `verify` → `archive-implementation` | 8 | 30 |
| Android | [`Android/app/`](Android/app/) | [`Android/specs/`](Android/specs/) | `propose` → `plan` → `implement` → `verify` → `archive-implementation` | 8 | 18 |
<!-- END GENERATED: README_CAPABILITIES -->

Матрица выше — производная проекция platform contracts. Канонические
capabilities и rule profiles находятся в
[`iOS/workflow/platform-contract.json`](iOS/workflow/platform-contract.json) и
[`Android/workflow/platform-contract.json`](Android/workflow/platform-contract.json),
а не в этом README.

## Харнес и runtime

- [`workflow/`](workflow/) — общие phases, rules, roles, scripts и templates;
- [`process/`](process/) — карта сущностей и потоков, не копия правил;
- [`.agents/skills/`](.agents/skills/) — portable skill SSOT;
- [`.codex/`](.codex/), [`.claude/`](.claude/), [`.cursor/`](.cursor/) и
  [`.opencode/`](.opencode/) — thin runtime bindings;
- [`iOS/workflow/`](iOS/workflow/) и [`Android/workflow/`](Android/workflow/) —
  platform addenda, profiles, rules и roles.

Основные входы: `brainstorming → discovery → elaborate` для общей продуктовой
проработки и `propose → plan → implement → verify → archive` для выбранной
платформы. Точный синтаксис и примеры находятся в [`workflow.md`](workflow.md).

Для product-backed UI Propose создаёт conditional `platform-ux.md`: shared
product layer фиксирует calm soft-blue semantic intent, а iOS адаптирует его
через evidence-backed Liquid Glass, Android — через Material 3 с conditional M3
Expressive. Technical-only/non-UI packages этот artifact не требуют.

## Hooks и лицензии

Runtime hooks делегируют общему
[`workflow/hooks/hook-runner.py`](workflow/hooks/hook-runner.py). Обязательный
staged gate запускает tracked [`.githooks/pre-commit`](.githooks/pre-commit)
только после явной настройки; автоматической установки нет. Third-party
provenance опубликован в [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) и
[`third_party/NOTICE.md`](third_party/NOTICE.md); тексты лицензий хранятся
отдельно и не дублируются в документации.

Root-документы объясняют систему и содержат generated projections. Процессный
канон остаётся в `workflow/`, platform contracts/addenda и `process/`.
