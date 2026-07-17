# Проверка — my-profile / Android / my-profile

## Strategy

Фаза verify выполнена свежим чтением текущих контрактов, production code, плана,
evidence и selected rules. Производственный код во время verify не менялся.
Локальные проверки и runtime-команды на эмуляторе `Pixel_6` завершились
успешно, поэтому все terminal rows получают `PASS`.

## Modularity verification

- Dependency graph: PASS
- Public API and visibility: PASS
- Module-level tests: PASS
- Consumer integration and build: PASS
- App-shell allowlist: PASS

Граф Gradle содержит отдельный `:my-profile`, приложение зависит от публичного
контракта профиля, `:app-shell` остаётся навигационной рамкой, а mutable state
профиля находится в `ProfileRoute` модуля `:my-profile`.

## Native UX verification

Нативные obligations проверены свежими локальными и connected evidence на
эмуляторе `Pixel_6`. Observation records находятся в `evidence/native-*.json`.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | evidence/native-pass-NATIVE-APPEARANCE.json | PASS |
| NATIVE-LIGHT | evidence/native-pass-NATIVE-LIGHT.json | PASS |
| NATIVE-DARK | evidence/native-pass-NATIVE-DARK.json | PASS |
| NATIVE-INCREASED-CONTRAST | evidence/native-pass-NATIVE-INCREASED-CONTRAST.json | PASS |
| NATIVE-ASSISTIVE-SEMANTICS | evidence/native-pass-NATIVE-ASSISTIVE-SEMANTICS.json | PASS |
| NATIVE-TEXT-SCALING | evidence/native-pass-NATIVE-TEXT-SCALING.json | PASS |
| NATIVE-MOTION | evidence/native-pass-NATIVE-MOTION.json | PASS |
| NATIVE-DEVICE-ADAPTATION | evidence/native-pass-NATIVE-DEVICE-ADAPTATION.json | PASS |
| NATIVE-AVAILABILITY-FALLBACK | evidence/native-pass-NATIVE-AVAILABILITY-FALLBACK.json | PASS |

## Contract matrix

| Contract ID | Verification dimension | Method | Evidence | Status |
|---|---|---|---|---|
| REQ-1 | profile-layout-content | Локальные проверки и проверка на эмуляторе для профиля. | evidence/verify-pass-runtime-my-profile.md | PASS |
| REQ-2 | interview-history-pagination | Модульные проверки repository. | evidence/verify-pass-local-commands.md | PASS |
| REQ-3 | my-interviews-enabled | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| REQ-4 | my-interviews-count-toast | Проверки обратной связи на эмуляторе и в интерфейсе. | evidence/verify-pass-runtime-my-profile.md | PASS |
| REQ-5 | my-interviews-empty-disabled | Проверки состояния и недоступного действия. | evidence/verify-pass-local-commands.md | PASS |
| REQ-6 | logout-empty-email-entry | Проверка интеграции приложения на эмуляторе и инспекция кода. | evidence/verify-pass-runtime-app.md | PASS |
| REQ-7 | recovery-no-private-data | Инспекция кода и проверка интеграции приложения на эмуляторе. | evidence/verify-pass-code-inspection.md | PASS |
| REQ-8 | cross-client-profile-parity | Поведение профиля Android на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| REQ-9 | assistive-profile-semantics | Нативное наблюдение на эмуляторе. | evidence/native-pass-NATIVE-ASSISTIVE-SEMANTICS.json | PASS |
| REQ-10 | adaptive-appearance | Нативное наблюдение на эмуляторе. | evidence/native-pass-NATIVE-TEXT-SCALING.json | PASS |
| AC-1 | profile-layout-content | Содержимое профиля на эмуляторе. | evidence/verify-pass-runtime-my-profile.md | PASS |
| AC-2 | interview-history-pagination | Модульные проверки repository. | evidence/verify-pass-local-commands.md | PASS |
| AC-3 | my-interviews-enabled | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AC-4 | my-interviews-count-toast | Проверки обратной связи на эмуляторе. | evidence/verify-pass-runtime-my-profile.md | PASS |
| AC-5 | my-interviews-no-navigation | Проверки приложения и профиля на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AC-6 | my-interviews-empty-disabled | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AC-7 | logout-empty-email-entry | Интеграция приложения на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AC-8 | logout-clears-profile-display | Интеграция приложения на эмуляторе и инспекция кода. | evidence/verify-pass-runtime-app.md | PASS |
| AC-9 | history-error-action-availability | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AC-10 | invalid-session-profile-recovery | Интеграция приложения на эмуляторе и инспекция кода. | evidence/verify-pass-runtime-app.md | PASS |
| AC-11 | logout-failure-recovery | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AC-12 | cross-client-profile-parity | Поведение Android на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AC-13 | assistive-profile-semantics | Нативное наблюдение. | evidence/native-pass-NATIVE-ASSISTIVE-SEMANTICS.json | PASS |
| AC-14 | assistive-feedback-states | Нативное наблюдение. | evidence/native-pass-NATIVE-ASSISTIVE-SEMANTICS.json | PASS |
| AC-15 | profile-text-scaling | Нативное наблюдение. | evidence/native-pass-NATIVE-TEXT-SCALING.json | PASS |
| AC-16 | profile-light-dark-appearance | Нативное наблюдение. | evidence/native-pass-NATIVE-LIGHT.json | PASS |
| AC-17 | profile-increased-contrast | Нативное наблюдение. | evidence/native-pass-NATIVE-INCREASED-CONTRAST.json | PASS |
| AC-18 | profile-non-color-cues | Нативное наблюдение. | evidence/native-pass-NATIVE-APPEARANCE.json | PASS |
| AND-REQ-1 | isolated-profile-capability | Инспекция кода и граф сборки. | evidence/verify-pass-code-inspection.md | PASS |
| AND-REQ-2 | shell-content-seam | Проверки потребителя оболочки. | evidence/verify-pass-local-commands.md | PASS |
| AND-REQ-3 | current-profile-loading | Проверки repository и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AND-REQ-4 | full-history-count | Модульные проверки repository. | evidence/verify-pass-local-commands.md | PASS |
| AND-REQ-5 | conditional-my-interviews | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AND-REQ-6 | count-feedback-no-navigation | Проверки профиля на эмуляторе. | evidence/verify-pass-runtime-my-profile.md | PASS |
| AND-REQ-7 | logout-auth-gate | Интеграция приложения на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AND-REQ-8 | material3-profile-screen | Нативное наблюдение. | evidence/native-pass-NATIVE-APPEARANCE.json | PASS |
| AND-REQ-9 | history-offline-recovery | Инспекция кода и проверки состояния. | evidence/verify-pass-code-inspection.md | PASS |
| AND-REQ-10 | invalid-session-cleanup | Интеграция приложения на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AND-REQ-11 | android-parity | Проверки приложения и профиля на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AND-REQ-12 | accessibility-localization-adaptive | Нативное наблюдение и инспекция ресурсов. | evidence/native-pass-NATIVE-ASSISTIVE-SEMANTICS.json | PASS |
| AND-AC-1 | gradle-module-boundary | Граф сборки и инспекция кода. | evidence/verify-pass-code-inspection.md | PASS |
| AND-AC-2 | shell-content-seam | Проверки потребителя оболочки. | evidence/verify-pass-local-commands.md | PASS |
| AND-AC-3 | profile-content | Содержимое профиля на эмуляторе. | evidence/verify-pass-runtime-my-profile.md | PASS |
| AND-AC-4 | pagination-completion | Модульные проверки repository. | evidence/verify-pass-local-commands.md | PASS |
| AND-AC-5 | enabled-action-positive-count | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AND-AC-6 | disabled-action-zero-unknown | Проверки состояния и интерфейса. | evidence/verify-pass-local-commands.md | PASS |
| AND-AC-7 | count-feedback | Обратная связь профиля на эмуляторе. | evidence/verify-pass-runtime-my-profile.md | PASS |
| AND-AC-8 | successful-logout-routing | Интеграция приложения на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AND-AC-9 | logout-failure-recovery | Проверки состояния, интерфейса и инспекция кода. | evidence/verify-pass-code-inspection.md | PASS |
| AND-AC-10 | invalid-session-cleanup | Интеграция приложения на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
| AND-AC-11 | material3-appearance | Нативное наблюдение. | evidence/native-pass-NATIVE-APPEARANCE.json | PASS |
| AND-AC-12 | assistive-semantics | Нативное наблюдение. | evidence/native-pass-NATIVE-ASSISTIVE-SEMANTICS.json | PASS |
| AND-AC-13 | font-scaling-layout | Нативное наблюдение. | evidence/native-pass-NATIVE-TEXT-SCALING.json | PASS |
| AND-AC-14 | localization-resources | Инспекция ресурсов и кода. | evidence/verify-pass-code-inspection.md | PASS |
| AND-AC-15 | cross-client-observable-parity | Проверки приложения и профиля на эмуляторе. | evidence/verify-pass-runtime-app.md | PASS |
