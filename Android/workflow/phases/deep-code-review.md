# Android addendum: Deep Code Review

Сначала использовать active package `engineering_scopes` и точный
`applicable_rule_files`. Без package/path-only review явно перечислить выбранные
risk lenses и причину каждого.

По evidence применять `android-kotlin-reviewer`,
`android-build-diagnostician`, `android-package-boundary-guard` и существующие
Kotlin, architecture, coroutines/Flow, Gradle, Compose, UI, accessibility,
localization и emulator rules. Compose/KMP/plugins/variants/tasks и `app`
module не предполагать; tools/commands только обнаруживать.

После requested fix terminal Verify unavailable. Результат Android review/bug
нельзя называть fixed или verified; эта read-only фаза lifecycle не запускает.
