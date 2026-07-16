# iOS implementation specifications

Активный iOS implementation package находится в
`iOS/specs/<feature>/changes/<change-id>/`: `meta.json`, `proposal.md`,
`implementation-spec.md`, `design.md`, `verification.md`, `plan/` и `evidence/`.
Архив находится в `iOS/specs/<feature>/archive/<YYYY-MM-DD-change-id>/`, а
active identity после архива содержит только `ARCHIVED.md`. Legacy-root package
не поддерживается. Для
`product-backed` она ссылается на `../../specs/product/<feature>/spec.md` со
статусами `READY` и `APPROVED`; общие REQ/AC не копируются и не
переопределяются. Product-backed intake также требует fresh
`review-verdicts.json`, принятый общим `validate-product-spec.py check`;
READY/APPROVED без receipt недостаточно. Для `technical-only` shared spec может быть `N/A` только при
явном `Product impact assessment: NONE` с evidence неизменности observable
behavior, REQ и AC. Любой найденный или неясный impact требует product
elaboration.

Публичный flow: `$propose ios <feature> [--change ...]` → `$plan` → `$implement`
→ `$verify` → `$archive implementation`. Переходы
проверяет [`validate-platform-change.py`](../../workflow/scripts/validate-platform-change.py).
Конкретный prefix/root/gates задаёт
[`platform-contract.json`](../workflow/platform-contract.json).
Шаблоны находятся в [`workflow/templates`](../../workflow/templates/).

`meta.json` содержит sorted `engineering_scopes` и exact
`applicable_rule_files`: union всех lifecycle phase bases и выбранных scope
profiles. Propose выбирает их по evidence, Plan может refine/add до `planned`,
затем сохраняет sealed selection в `plan/rule-selection.json`, после чего
Implement/Verify не расширяют набор. Fingerprint охватывает только этот набор
правил и semantic adapter projection выбранных profiles.
