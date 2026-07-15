# Android implementation specifications

Будущий `Android/specs/<feature>/changes/<change-id>/` будет содержать Android
implementation package. Для
`product-backed` она ссылается на `../../specs/product/<feature>/spec.md` со
статусами `READY` и `APPROVED`; общие REQ/AC не копируются и не
переопределяются. Для `technical-only` shared spec может быть `N/A` только при
явном `Product impact assessment: NONE` с evidence неизменности observable
behavior, REQ и AC. Любой найденный или неясный impact требует product
elaboration.

Шаблон: [`platform-implementation-spec.md`](../../workflow/templates/platform-implementation-spec.md).

Сейчас Android implementation adapter и architecture layer не реализованы. Любой
вызов должен вернуть `NOT IMPLEMENTED` без создания package.
