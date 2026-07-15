# Product elaboration skills — test evidence

## Scope

Cross-platform hard change: portable skills `brainstorming`, `discovery` и
`elaborate`, общий product package, UX/review/approval gates и граница будущих
iOS/Android implementation specs.

## RED: observed failures

### Missing product-layer contract

До изменения в харнесе отсутствовали entry points трёх product-elaboration
skills и канонический контракт, который определяет общий product SSOT, границу
fan-out и запрет платформенного переопределения REQ/AC.

### Duplicate runtime namespace

Claude Code adapters находились в `.claude/skills/<name>/SKILL.md` одновременно
с portable `.agents/skills/<name>/SKILL.md`. OpenCode сканирует оба namespace;
шесть последовательных discovery-прогонов возвращали смесь locations. Поэтому
portable SSOT выбирался недетерминированно.

### Behavioral approval failure

Первичный forward-test до fix сформировал результат со статусом `READY` без
явного human product approval. Это реальный behavioral RED: одних полных
requirements/reviews недостаточно для разрешения fan-out.

### Incomplete product elaboration

В первой версии отсутствовали обязательный UI-only shared `ux.md`, применимые
product review lenses и evidence явного product approval. Screen/flow impact
мог молча уехать в downstream platform specification.

## GREEN: implemented architecture

- `specs/product/<feature>/` определён как общий пакет: опциональный
  `concept.md`, `brief.md`, UI-only `ux.md` и `spec.md`.
- Discovery обязан подготовить draft journey, screen/flow impact, secondary
  states, accessibility/localization, analytics/privacy и shared design-system
  intent до downstream.
- Elaborate создаёт `ux.md` для UI/interaction scope, проводит applicable
  product, UX/accessibility, design-system, data/analytics/privacy, security и
  cross-client parity reviews и сохраняет findings/gaps.
- `READY` требует полного REQ↔AC coverage, применимого UX artifact/review,
  закрытых blockers и `Product approval: APPROVED` с approver/evidence. Без
  явного решения обязательный результат — `DRAFT / PENDING APPROVAL`.
- Platform architecture, SDK/module details, requirement→tests mapping,
  implementation, migration и rollout остаются downstream.
- Platform intake разделён на `product-backed` (`READY` + `APPROVED`) и
  `technical-only` (`Product impact assessment: NONE` + evidence). Найденный
  или неясный behavioral impact запрещает bypass и возвращает задачу в product
  elaboration.
- Claude Code сохраняет явный `/<skill>` UX через `.claude/commands/<name>.md`;
  одноимённые `.claude/skills` удалены, portable SSOT остаётся в `.agents/skills`.
- Harness lint проверяет Claude command parity, запрещает duplicate Claude
  skills и проверяет structural artifacts/tokens product pipeline.

## Specification/proposal boundary

| Завершается до fan-out | Остаётся downstream |
|---|---|
| Problem/why, outcomes/success, scope/non-goals | Platform architecture и implementation design |
| Product decisions, journey/flow и shared design-system intent | SDK/framework/module details |
| Shared behavior, REQ и numbered AC | Platform constraints и requirement→tests mapping |
| Common constraints, reviews, approval и open questions | Implementation, migration и rollout plan |

## Behavioral forward tests

### Brainstorming: component comparison — PASS

- **Вход:** сравнить три варианта компонента до выбора продуктового решения.
- **Observed routing:** применён только `brainstorming`; сформированы три
  варианта и next step `discovery`.
- **Status/artifacts:** pre-spec, статуса нет; допустим только optional shared
  `concept.md`; platform specs не создавались.
- **Verdict:** `PASS`.

### Discovery: spacing-token training — PASS

- **Вход:** общий учебный flow с Android tactile API/min-version constraint.
- **Observed routing:** создан только shared brief/draft flow; haptic остался
  optional, общий observable behavior сохранён, Android constraint передан в
  downstream направления.
- **Status/artifacts:** `READY` не выставлялся; platform specs не создавались.
- **Verdict:** `PASS`.

### Elaborate: incomplete UI package — PASS

- **Вход:** UI brief с непокрытым `REQ-3`, privacy blocker для free text и без
  явного product approval.
- **Observed routing:** потребованы shared `ux.md` и applicable review lenses;
  coverage gap, privacy finding и approval gate остались blockers.
- **Status/artifacts:** `DRAFT / PENDING APPROVAL`; platform specs не
  создавались.
- **Verdict:** `PASS` для uncovered REQ, applicable review blocker и no-approval
  поведения.

### Android Gradle plugin: technical-only — RED → GREEN

- **Вход:** обновление Android Gradle plugin без изменения observable behavior.
- **Observed routing:** все product skills корректно bypass-нуты — routing
  `PASS`.
- **RED:** downstream template и platform README безусловно требовали shared
  `READY`/`APPROVED` spec и не описывали technical-only intake.
- **GREEN:** добавлены режимы `product-backed` и `technical-only`. Последний
  разрешён без shared spec только при `Product impact assessment: NONE` с
  evidence неизменности observable behavior, REQ и AC; `PRESENT`/`UNCERTAIN`
  reroute в product elaboration.

## Platform evidence

### iOS

- implementation root: `iOS/specs/<feature>/`;
- в spacing-token scenario отдельно проверен полный визуальный, текстовый и
  accessibility outcome без обязательного haptic — `PASS`;
- platform-specific tactile constraint не ослабил общий iOS product outcome;
- `product-backed` требует shared `READY`/`APPROVED`, а `technical-only` —
  доказанный `Product impact assessment: NONE`.

### Android

- implementation root: `Android/specs/<feature>/`;
- в spacing-token scenario haptic остался optional, API/min-version constraint
  передан downstream без fork общего поведения — `PASS`;
- Gradle plugin scenario корректно bypass-нул product skills — routing `PASS`;
- исправленный `technical-only` intake требует evidence неизменности observable
  behavior, REQ и AC.

## Structural verification

- `harness-lint.py --warn-as-error` — grade A, 0 critical, 0 warnings;
- `quick_validate.py` — `Skill is valid!` для всех шести portable skills;
- шесть последовательных `opencode debug skill` прогонов разрешили все шесть
  имён только из `.agents/skills/`; смешанных locations после удаления
  `.claude/skills` нет;
- Claude commands присутствуют 6/6, передают `$ARGUMENTS` и ссылаются на
  portable skill; duplicate skill namespace отсутствует;
- OpenCode commands и portable skills присутствуют 6/6;
- 12 portable/Claude metadata файлов успешно разобраны как YAML;
- structural assertions подтвердили UX/review/approval gates и оба platform
  intake mode с обязательным impact evidence для `technical-only`;
- safe scans не нашли запрещённых project references, legacy dependencies или
  trailing whitespace в изменённых канонах/adapters.

Structural checks дополняют, но не заменяют фактические behavioral verdicts
выше.

## Остаточные ограничения

- Content-level parser реального feature package пока отсутствует; до его
  появления соблюдение UX/review/approval gates обеспечивается skill contract и
  шаблонами.
- Downstream platform specification skill ещё не перенесён; его будущий
  контракт обязан реализовать оба intake mode и не допускать `technical-only`
  bypass при behavioral impact.
