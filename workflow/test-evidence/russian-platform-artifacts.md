# Russian platform artifacts — RED → GREEN → REFACTOR

Дата: 2026-07-16. Scope: cross-platform hard rule.

## RED

До изменения current v1 package мог пройти structural validation с полностью
английским authored prose. Whole-file Cyrillic marker также позволял одному
русскому padding paragraph скрыть English sections.

Последующие pressure reviews выявили отдельные обходы: narrative table cells и
Markdown link labels не проверялись; соседние list items склеивались; leaf-only
symlink check пропускал ancestor symlink; machine-row continuation наследовал
exemption; invalid UTF-8 молча удалялся через `errors="ignore"`; typed authored
lifecycle reports под `evidence/` не входили в language surface.

Writer-owned harness path set не включает specs/production. Active platform
packages и concurrent implementation commits не используются как byte-stable
fixture и не редактируются harness writer.

## GREEN

Common `workflow/rules/artifact-language.md` входит во все current v1 phase
profiles обоих adapters; registry-anchored v0 exempt. Validator проверяет каждый
authored block после точных machine/code/path exclusions и требует meaningful
Cyrillic с Cyrillic-dominant residual prose. Diagnostic bounded одной строкой на
файл, содержит только path и первые номера blocks, без content.

Safe boundary получает exact package path, требует lexical/resolved containment,
resolved package внутри repo, запрещает каждый symlink component от package до
authored file, требует regular file и strict UTF-8 decode.

## Pressure combinations

Одинаковые direct fixtures выполняются в контексте реальных iOS и Android
adapters:

1. English prose, English section после русского padding и English paragraph
   внутри русского документа — `BLOCK`.
2. Русский technical prose с SwiftUI/Liquid Glass/Material 3/Gradle — `PASS`;
   exact machine rows/IDs/paths — `PASS`.
3. English narrative table cell — `BLOCK`; русский cell — `PASS`; separator,
   header и machine-only cells — `PASS`.
4. English Markdown link label — `BLOCK`; русский label и raw official URL —
   `PASS`; URL target не считается prose.
5. Каждый bullet/numbered item независим; русский item не скрывает соседний
   English item. Continuation принадлежит своему authored item.
6. Exemption exact machine-row действует только на саму строку: English
   indented continuation — `BLOCK`, русский — `PASS`.
7. Leaf/ancestor/package symlink, non-regular file, traversal/outside containment
   — `BLOCK`; обычный nested plan file — `PASS`.
8. Invalid UTF-8 — одна path-only `BLOCK` diagnostic; valid UTF-8 — `PASS`.
9. Восемь English blocks дают одну bounded diagnostic с `(+5 more)`.

## Typed authored reports

Без rglob выбираются только direct children:

- `evidence/task-[0-9]{3}.md`;
- `evidence/reconciliation-<YYYYMMDD>T<HHMMSS>Z-task-NNN[-<safe-slug>].md`
  по exact canonical regex.

English task и reconciliation reports независимо дают `BLOCK`, русские —
`PASS`. Typed leaf/ancestor symlink и invalid UTF-8 остаются `BLOCK` той же safe
boundary. Произвольные `runtime-output.md`, `.log`, JSON, screenshots и внешний
raw evidence не выбираются, не требуют перевода и не могут служить padding.
Правило действует во всех current v1 validator modes; v0 exempt.

## REFACTOR и ограничения

Эвристика не оценивает качество перевода или semantic truth. Exact schema,
contract IDs, paths, code/API names и raw tool output сохраняются без перевода.
Расширение exclusions или authored families требует отдельного RED scenario и
harness review.

Root documentation disposition: semantic policy `README.md` — `no-impact`;
marked generated projections обновляются `harness-docs.py render` только при
изменившемся repository inventory. `workflow.md` и `deep-info.md` — `update` для
operational и manual parity.

Stable snapshot относится только к writer-owned harness path set. Specs,
production и moving concurrent paths исключены из byte-stability/ownership
claims финального harness audit.
