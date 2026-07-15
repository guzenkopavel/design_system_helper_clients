# Android addendum: Pre-commit Check

Gradle wrapper/settings/modules/plugins/variants/tasks обнаруживаются из repo/CI.
Не предполагать `app`, `assembleDebug`, `testDebugUnitTest`, detekt, lintDebug,
KMP, Compose или Hilt. Resources/accessibility/UI требуют task evidence и
emulator/runtime evidence только для соответствующих paths. Greenfield
отсутствие project/tooling даёт N/A или risk-based UNKNOWN.
