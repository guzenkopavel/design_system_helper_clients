# Android addendum: Plan

Задачи используют обнаруженные wrapper/tasks/plugins/variants. Не придумывать
`build`, detekt, ktlint, Compose, Hilt или KMP. UI tasks включают
emulator/accessibility/design-system; `compose` требует отдельный `ui` scope и
Compose-state check. Concurrency требует cancellation/lifecycle; module/Gradle
scopes фиксируют точные boundaries/tasks. Multiplatform остаётся отдельным
evidence-selected scope.
Product-backed UI tasks ссылаются на `platform-ux.md` и содержат все adapter
native UX checks для Material 3, appearances и fallback.
