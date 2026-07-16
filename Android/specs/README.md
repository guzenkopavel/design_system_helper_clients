# Android implementation specifications

`Android/specs/<feature>/changes/<change-id>/` содержит Android
implementation package. Для
`product-backed` она ссылается на `../../specs/product/<feature>/spec.md` со
статусами `READY` и `APPROVED`; общие REQ/AC не копируются и не
переопределяются. Product-backed intake также требует fresh
`review-verdicts.json`, принятый общим `validate-product-spec.py check`;
READY/APPROVED без receipt недостаточно. Для `technical-only` shared spec может быть `N/A` только при
явном `Product impact assessment: NONE` с evidence неизменности observable
behavior, REQ и AC. Любой найденный или неясный impact требует product
elaboration.

Шаблон: [`platform-implementation-spec.md`](../../workflow/templates/platform-implementation-spec.md).

Adapter поддерживает полный implementation lifecycle. После завершения tasks
package остаётся `implementing` до fresh `$verify android ...`; только exact
PASS evidence/fingerprint допускает `verified` и последующий
`$archive implementation android ...`. Команды и infrastructure обнаруживаются
из repository/Plan, а archive не изменяет shared product package.
