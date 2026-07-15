# iOS implementation specifications

`iOS/specs/<feature>/` содержит iOS implementation package: `meta.json`,
`proposal.md`, `implementation-spec.md`, `design.md`, `verification.md` и после
`plan` — `plan/`. Для
`product-backed` она ссылается на `../../specs/product/<feature>/spec.md` со
статусами `READY` и `APPROVED`; общие REQ/AC не копируются и не
переопределяются. Для `technical-only` shared spec может быть `N/A` только при
явном `Product impact assessment: NONE` с evidence неизменности observable
behavior, REQ и AC. Любой найденный или неясный impact требует product
elaboration.

Публичный flow: `$propose ios <feature>` → `$plan ios <feature>`. Переходы
проверяет [`validate-platform-change.py`](../../workflow/scripts/validate-platform-change.py).
Конкретный prefix/root/gates задаёт
[`platform-contract.json`](../workflow/platform-contract.json).
Шаблоны находятся в [`workflow/templates`](../../workflow/templates/).
