# Android addendum: Plan

Задачи используют обнаруженные wrapper/tasks/plugins/variants. Не придумывать
`build`, detekt, ktlint, Compose, Hilt или KMP. UI tasks включают
emulator/accessibility/design-system; `compose` требует отдельный `ui` scope и
Compose-state check. Concurrency требует cancellation/lifecycle; module/Gradle
scopes фиксируют точные boundaries/tasks. Multiplatform остаётся отдельным
evidence-selected scope.
Product-backed UI tasks ссылаются на `platform-ux.md` и содержат все adapter
native UX checks для Material 3, appearances и fallback.

Для isolated boundary задачи с `Boundary owner` материализуют только
обнаруженные settings/module wiring, minimal public contract/visibility tests,
module-level tests, consumer integration/build, dependency graph и app-shell
wiring. Module names, variants и Gradle tasks не придумывать.
