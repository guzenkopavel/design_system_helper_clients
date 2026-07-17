# Terminal verification evidence — user-profile-auth-public-contract-repair

Дата свежей проверки: `2026-07-17T03:09:42Z`.

Выбранная identity: `ios/user-profile-auth/user-profile-auth-public-contract-repair`.
Проверка выполнена для текущего сервера по умолчанию `https://89.125.1.21.nip.io`;
UI-сценарии авторизации используют детерминированный stub-режим приложения, чтобы
проверять registration/login flow без изменения живого backend state.

## Scope baseline

- `verify-scope-baseline.json`: `617143558603b1a83e47efccd10ac20a256d2ed12515bf5635583e532195fe05`.
- До terminal writes production/task/plan/contracts/rules были зафиксированы
  verify baseline. После записи verification/evidence/meta будет выполнен
  `validate-implementation-scope.py verify-check` с этим SHA.

## Fresh commands

1. `xcodebuild test -scheme AuthFeature -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5'`
   через `workflow/scripts/test-watchdog.sh`.
   Результат: `TEST SUCCEEDED`, `45 tests`, `0 failures`.
   Покрытие: фабрика, публичный контракт, session model, email/password validation,
   retryable/offline state, invalid session cleanup, Keychain secret store, HTTPS
   configuration, error envelope, rate-limit envelope, cookie token extraction,
   login/register use cases и concurrency/isolation checks.

2. `xcodebuild -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build`
   через `workflow/scripts/test-watchdog.sh`.
   Результат: `BUILD SUCCEEDED`.
   Target dependency graph подтверждает направление:
   `SysDevScen -> AuthFeature -> AuthFeature`.

3. `xcodebuild test -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/AuthFlowUITests`
   через `workflow/scripts/test-watchdog.sh`.
   Результат: `TEST SUCCEEDED`, `6 tests`, `0 failures`.
   Наблюдения: signed-out launch показывает `auth.email`/`auth.continue` и скрывает
   tabs shell; existing email ведёт на «Вход»; new email ведёт на «Регистрация»;
   back сохраняет email; successful login открывает «Кейсы»; successful
   registration открывает «Кейсы».

4. `xcodebuild test -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/AppShellUITests`
   через `workflow/scripts/test-watchdog.sh`.
   Результат: `TEST SUCCEEDED`, `3 tests`, `0 failures`.
   Наблюдения: active stub session сразу показывает shell с «Кейсами», навигация
   «Кейсы»/«Знания»/«Профиль» доступна, прежние template controls отсутствуют.

5. `xcodebuild test -project SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/SysDevScenUITestsLaunchTests`
   через `workflow/scripts/test-watchdog.sh`.
   Результат: `TEST SUCCEEDED`, `4 tests`, `0 failures`.
   Наблюдения: Xcode launch matrix выполнил Portrait/Light, Landscape/Light,
   Portrait/Dark, Landscape/Dark; каждый запуск добавил attachment `Launch Screen`.

Недействительные попытки: начальный монолитный `-only-testing:SysDevScenUITests`
и один ранний focused запуск были остановлены как silent runner hang до test output.
Они не использованы как PASS evidence; terminal PASS основан только на свежих
успешных focused прогонах выше.

## Static inspections

- Application target использует auth через публичный пакет: `SysDevScenApp.swift`
  создаёт `AuthConfiguration` и `AuthSessionModel` через `AuthFeatureFactory`,
  `RootView.swift` переключает `SessionState` и передаёт `AuthSessionModel` в
  `AuthFlowView`.
- В application target нет реализации auth data/network/storage: Keychain,
  URLSession client, use cases и ViewModel остаются внутри `iOS/AuthFeature`.
- `AuthFeatureFactoryTests.test_publicTopLevelContract_containsOnlyApprovedTypes`
  подтвердил минимальную верхнеуровневую публичную поверхность пакета.
- Source не добавляет custom animation/transition, custom blur/material fallback
  или appearance-specific literals для auth flow; используются стандартные SwiftUI
  controls, semantic labels и accessibility identifiers.

## Contract coverage notes

- Shared `REQ-1`/`AC-1` и `IOS-AC-4`: signed-out UI launch показывает auth email
  step и не показывает tabs shell.
- Shared `REQ-2`/`AC-2`/`AC-3`/`AC-4` и `IOS-AC-6`: UI tests покрывают email-first
  branching на «Вход»/«Регистрация» и возврат к email с сохранением значения.
- Shared `REQ-3`/`AC-5`/`AC-6` и `IOS-AC-7`: successful login и successful
  registration немедленно открывают shell с активными «Кейсами».
- Shared `REQ-4`/`AC-7`: session model tests подтверждают valid-session start, а
  AppShell UI tests подтверждают active stub launch directly into shell.
- Shared `REQ-5`, `AC-8`–`AC-14`, `IOS-AC-8`–`IOS-AC-11`: package tests покрывают
  local validation, invalid credentials/error envelope mapping, short password,
  rate-limit envelope, retryable/offline state и explicit retry surface.
- Shared `REQ-6`, `AC-15`/`AC-16`, `IOS-AC-12`: session/use-case tests покрывают
  invalid session, возврат в signed-out и очистку секрета.
- Shared `REQ-7`, `AC-17`/`AC-18`, `IOS-AC-13`: Keychain store tests покрывают
  сохранение/загрузку/перезапись/removal только session secret; password storage
  path в реализации отсутствует.
- Shared `REQ-8`, `AC-19`–`AC-24`, `IOS-AC-2`: UI tests взаимодействуют через
  видимые русские labels и `auth.*` identifiers; launch matrix покрывает light/dark
  и device orientation smoke; static source inspection подтверждает отсутствие
  color-only custom states, custom motion и custom transparency dependency.
- Shared `REQ-9`, `AC-25`, `IOS-AC-17`: UI flow labels и ordering совпадают с
  общим контрактом: «Авторизация» → email → «Вход»/«Регистрация» → «Кейсы».
- `IOS-REQ-1`, `IOS-REQ-12`, `IOS-AC-1`, `IOS-AC-16`: app-shell остаётся
  composition shell, auth живёт в отдельном Swift package, dependency graph
  направлен от app target к package.
- `IOS-REQ-10`, `IOS-AC-14`: API client tests подтверждают HTTPS-only config,
  decoding error envelope, cookie token extraction и response decoding для
  email-check/login/register.
- `IOS-REQ-11`, `IOS-AC-15`: session start idempotence и MainActor-bound state
  проверены package tests; повторная отправка в UI блокируется состоянием `isSubmitting`.

## Modularity verification

- Dependency graph: `PASS` — fresh app build вывел `SysDevScen -> AuthFeature`.
- Public API and visibility: `PASS` — package tests подтвердили approved public
  top-level contract.
- Module-level tests: `PASS` — `AuthFeature` package: 45/45.
- Consumer integration and build: `PASS` — `SysDevScen` app build succeeded.
- App-shell allowlist: `PASS` — application target содержит entry/lifecycle/root
  routing/DI/config/resources, auth internals остаются в package.
