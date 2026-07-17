# Fresh verification evidence — Android user-profile-auth

Итог: свежая проверка Android `user-profile-auth` на Pixel_6 AVD / API 36 завершилась успешно. Все проверенные runtime, UI, accessibility, security, module-boundary и live backend-contract observations получили `PASS`.

## Среда

- Дата проверки: 2026-07-17T03:13:08Z.
- Platform package: `Android/specs/user-profile-auth/changes/user-profile-auth`.
- Устройство: `emulator-5554`, `Pixel_6(AVD)`, Android API `36`.
- Backend: `https://89.125.1.21.nip.io/`.
- Verify baseline: `evidence/verify-scope-baseline.json`.

## Команды и результаты

| Method | Command | Observation |
|---|---|---|
| Unit and androidTest compile | `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 180 --max-output-lines 5000 -- ./Android/gradlew -p Android --no-daemon :auth:testDebugUnitTest :app:testDebugUnitTest :auth:compileDebugAndroidTestKotlin :app:compileDebugAndroidTestKotlin --console=plain` | `BUILD SUCCESSFUL`; auth/app unit checks and androidTest Kotlin compilation completed. |
| Auth UI runtime | `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 180 --max-output-lines 5000 -- ./Android/gradlew -p Android --no-daemon :auth:connectedDebugAndroidTest --console=plain` | `BUILD SUCCESSFUL`; `24 tests on Pixel_6(AVD) - 16`, `0 failed`. |
| App auth integration runtime | `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 300 --max-output-lines 7000 -- ./Android/gradlew -p Android --no-daemon :app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=ru.home.sysdevsc.AuthIntegrationTest --console=plain` | `BUILD SUCCESSFUL`; `7 tests on Pixel_6(AVD) - 16`, `0 failed`. |
| App shell and accessibility runtime | `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 300 --max-output-lines 7000 -- ./Android/gradlew -p Android --no-daemon :app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=ru.home.sysdevsc.AppShellIntegrationTest,ru.home.sysdevsc.AuthAccessibilityTest --console=plain` | `BUILD SUCCESSFUL`; `11 tests on Pixel_6(AVD) - 16`, `0 failed`. |
| Gradle graph | `rtk ./Android/gradlew -p Android --no-daemon :projects --console=plain` | `BUILD SUCCESSFUL`; graph contains physical modules `:app`, `:app-shell`, `:auth`. |
| Emulator availability | `rtk /Users/pavel/Library/Android/sdk/platform-tools/adb shell getprop ro.build.version.sdk && rtk /Users/pavel/Library/Android/sdk/platform-tools/adb devices -l` | Device online as `emulator-5554`; SDK `36`. |
| Live backend email-check | `rtk curl -i -sS --max-time 10 -H 'Content-Type: application/json' -d '{"email":"verify-smoke-20260717@example.com"}' https://89.125.1.21.nip.io/api/auth/email-check` | HTTP `200`; response `{"email":"verify-smoke-20260717@example.com","exists":false,"nextStep":"register"}`. No account was created. |
| Manifest/network static inspection | `rtk sed -n '1,80p' Android/app/src/main/AndroidManifest.xml && rtk sed -n '1,120p' Android/app/src/main/res/xml/network_security_config.xml` | Manifest contains `android.permission.INTERNET`; application uses `@xml/network_security_config`; `cleartextTrafficPermitted="false"`. |

## Runtime coverage observations

- `AuthIntegrationTest.noSessionStartsAtEmailStepWithRealPlatformContext` confirms auth gate starts at email step without a session and does not expose AppShell.
- `AuthIntegrationTest.emailCheckMovesToPasswordStep` confirms email-first branching into the password step for an existing account.
- `AuthIntegrationTest.successfulLoginOpensCasesAndPersistsSession` confirms login invokes `login()`, stores the session secret and opens AppShell with `Кейсы`.
- `AuthIntegrationTest.newEmailRegistrationOpensCasesAndPersistsSession` confirms registration invokes `register()`, does not invoke `login()`, stores the session secret and opens AppShell with `Кейсы`; the registration action label is `Зарегистрироваться`.
- `AuthIntegrationTest.persistedSessionSurvivesRepositoryReconstructionAndActivityRecreation` confirms persisted session recovery after repository reconstruction/activity recreation.
- `AuthIntegrationTest.repositoryReportedExpiryClearsBoundaryAndReturnsToEmailStep` confirms expired repository state returns to email step and clears the boundary.
- `AuthIntegrationTest.applicationBoundaryRejectsCleartextTraffic` confirms cleartext traffic rejection.
- `AuthScreenTest` covers email/password field rendering, login/register titles, visible contextual email, local validation errors, server/offline/rate-limit errors, loading indicators, back transition, accessibility field names and rate-limit button disabled state.
- `AuthAccessibilityTest` covers visible labels, password/action accessible names and roles, registration title and registration action, focus transfer, validation/error semantics, non-color cues, 200% text scale, light/dark readable roles and soft-blue fallback.
- `AppShellIntegrationTest` covers approved shell destinations and destination transitions after authenticated entry.

## Static architecture and security observations

- `Android/settings.gradle.kts` includes `:app`, `:app-shell` and `:auth`, establishing physical modules rather than folders-only isolation.
- `Android/app/build.gradle.kts` depends on `project(":app-shell")` and `project(":auth")`; app shell composition is centralized in `MainActivity.kt` / `SysDevScApp()`.
- `Android/auth/build.gradle.kts` is a library module with Compose, ViewModel, OkHttp and AndroidX Security Crypto dependencies.
- `EncryptedSessionRepository` stores only `session_token` through `EncryptedSharedPreferences` with `MasterKey` and does not store password material.
- `DefaultAuthApiService` uses HTTPS base URL normalization, `/api/auth/email-check`, `/api/auth/login`, `/api/auth/register`, bounded OkHttp timeouts, `Set-Cookie` extraction for `dsh_session`, and maps 401/409/422/429/offline outcomes to domain results.
- `Android/app/src/main/AndroidManifest.xml` declares `android.permission.INTERNET`, uses `networkSecurityConfig`, and keeps exactly one exported launcher `MainActivity`.

## Contract row coverage

- `REQ-1`–`REQ-9`: covered by app auth integration, auth UI runtime, accessibility runtime, security/static inspection, Gradle graph and live backend email-check.
- `AC-1`–`AC-25`: covered by `AuthIntegrationTest`, `AuthScreenTest`, `AuthAccessibilityTest`, `AuthInputValidatorTest`, `AuthStateTest`, static security inspection and live backend email-check.
- `AND-REQ-1`–`AND-REQ-10`: covered by Gradle graph/static module inspection, app/auth connected tests, unit tests, security inspection and accessibility tests.
- `AND-AC-1`–`AND-AC-30`: covered by the same exact Android method set; native-specific appearance/accessibility rows are backed by the observation JSON records in this evidence directory.
- `NATIVE-*`: exact observation records are stored in `evidence/native-*.json`; every record points back to this raw evidence file as its underlying reference.

## Modularity verification

- Dependency graph: `PASS`; Gradle reports `:app`, `:app-shell`, `:auth`.
- Public API and visibility: `PASS`; `AuthGate`, `AuthApiService` and `SessionRepository` form typed seams, while implementation classes remain inside `:auth`.
- Module-level tests: `PASS`; `:auth:testDebugUnitTest` and `:auth:connectedDebugAndroidTest` passed.
- Consumer integration and build: `PASS`; `:app` unit/compile and connected integration tests passed.
- App-shell allowlist: `PASS`; `SysDevScApp()` only composes root auth gating and AppShell destination state.

## Native UX verification

- Appearance: `PASS`; Material 3 `OutlinedTextField`, tonal primary action, supporting error text, registration/login titles and visible contextual email are exercised by runtime tests.
- Light/dark: `PASS`; `AuthAccessibilityTest.lightAndDarkMaterialRolesHaveAccessibleOnColors` passed.
- Increased contrast: `PASS`; accessible on-color contrast checks and non-color cues passed.
- Assistive semantics: `PASS`; visible labels, roles, focus and error semantics passed.
- Text scaling: `PASS`; 200% font scale scenario passed.
- Motion: `PASS`; loading/rate-limit states have text/indicator cues and do not rely on animation as the only state carrier.
- Device adaptation: `PASS`; Pixel 6 compact runtime and increased text scale remained discoverable.
- Availability fallback: `PASS`; dynamic color disabled / soft-blue fallback scenario passed.
