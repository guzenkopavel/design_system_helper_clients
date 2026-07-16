# Android design system

Использовать существующие tokens/components/themes. Не создавать параллельный
token SSOT; отклонение фиксируется как platform decision. Для product-backed
`ui` package создать `platform-ux.md` по общему template.

Material 3 — baseline: MaterialTheme, color/typography/shapes, semantic tonal
roles, accessible on-colors и light/dark appearances. M3 Expressive — только
conditional extension при подтверждённых repository SDK/dependency/product
evidence; никогда не предполагать поддержку. Dynamic color — явное
product/platform decision: Android 12+ availability обнаруживается, а не
предполагается; персонализация может уйти от blue, поэтому всегда нужен
accessible soft-blue fallback. Verification покрывает accessibility,
localization, motion, device/layout states и fallback.

Official reference:
- https://developer.android.com/develop/ui/compose/designsystems/material3
