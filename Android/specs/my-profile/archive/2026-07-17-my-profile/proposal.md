# Proposal — my-profile / Android / my-profile

## Intake

- Change type: product-backed
- Shared product spec: `specs/product/my-profile/spec.md`
- Product status / approval: READY / APPROVED
- Product impact assessment: PRESENT
- Evidence: `specs/product/my-profile/spec.md` имеет `READY`, `APPROVED`, явное approval evidence и зелёный `review-verdicts.json`; `validate-product-spec.py check --feature my-profile` вернул `PASS`.
- Tier: standard

## Goal

Создать Android implementation package для авторизованной вкладки профиля. Платформа должна показать email текущего аккаунта, крупный стандартный профильный символ, действия «Мои интервью» и «Выход», полный счётчик истории интервью через постраничную загрузку и корректное возвращение в auth-флоу после успешного logout.

## Scope

В область входят новая Android-возможность профиля, её Compose UI, repository boundary для `GET /api/profile`, `GET /api/interviews/history` и `POST /api/auth/logout`, корневая интеграция с существующими `:app`, `:auth` и `:app-shell`, русские строковые ресурсы, состояния представления Material 3, матрица будущей проверки и модульная граница Gradle. Поведение зависит от доставленного baseline `user-profile-auth`, который уже отвечает за auth gate, восстановление сессии и очистку недействительной сессии.

## Engineering scope selection

- Selected scopes: `application`, `compose`, `concurrency`, `gradle`, `localization`, `module`, `ui`.
- Evidence for each scope: `application` выбран из-за изменения корневой композиции между auth state, profile destination оболочки и восстановлением после logout; `module` выбран по strong default для новой самостоятельной функции с data/network/UI; `ui` и `compose` выбраны из-за нового профильного экрана Material 3; `concurrency` выбран из-за последовательной постраничной загрузки истории, отмены задач и logout; `gradle` выбран из-за новой библиотечной единицы и настройки зависимостей; `localization` выбран из-за русских пользовательских текстов и форматированного сообщения «Интервью: N».
- Considered but not selected: `multiplatform` не выбран, потому что Android package не меняет общий Kotlin Multiplatform слой; `delivery` не выбран, потому что propose не создаёт commit или rollout; `developer-experience` не выбран, потому что tooling feedback не является самостоятельной частью изменения.

## Applicable rule files

Точный lifecycle union из баз фаз и выбранных scopes:

```text
- `workflow/rules/specification-layers.md`
- `workflow/rules/artifact-language.md`
- `workflow/rules/system-design.md`
- `workflow/rules/system-design/modularity.md`
- `Android/workflow/rules/architecture.md`
- `Android/workflow/rules/architecture/modularization.md`
- `workflow/rules/coding-standards.md`
- `workflow/rules/tdd-first.md`
- `workflow/rules/test-execution.md`
- `workflow/rules/verification-matrix.md`
- `workflow/rules/code-comments.md`
- `Android/workflow/rules/kotlin-style.md`
- `Android/workflow/rules/android-pitfalls.md`
- `Android/workflow/rules/architecture/data-layer.md`
- `Android/workflow/rules/architecture/ui-layer.md`
- `Android/workflow/rules/architecture/domain-layer.md`
- `Android/workflow/rules/architecture/dependency-injection.md`
- `Android/workflow/rules/unit-testing.md`
- `Android/workflow/rules/compose.md`
- `Android/workflow/rules/coroutines-flows.md`
- `Android/workflow/rules/gradle-build.md`
- `Android/workflow/rules/localization.md`
- `Android/workflow/rules/ui-testing.md`
- `Android/workflow/rules/accessibility.md`
- `Android/workflow/rules/ui-design-system.md`
- `Android/workflow/rules/emulator.md`
```

## Non-goals

Пакет не добавляет экран списка интервью, детали интервью, редактирование профиля, пользовательский аватар, новые analytics events, backend changes, изменение auth API, изменение двух остальных вкладок оболочки, новый DI framework, Dynamic color как обязательное поведение или production code в phase propose.

## Existing context

Обнаружены доставленные Android документы базовой линии `Android/specs/app-shell/SPECIFICATION.md` и `Android/specs/user-profile-auth/SPECIFICATION.md`. Граф Gradle содержит три проекта `:app`, `:app-shell` и `:auth`; точка входа компонует `AuthGate` и `AppShell`, а оболочка уже имеет направление `Profile`, но пока показывает общий временный контент. Каталог версий содержит уже выбранные зависимости Material 3, Compose, lifecycle ViewModel, coroutines, OkHttp, Moshi и security crypto.

## Proposed greenfield paths

```text
- `Android/my-profile/build.gradle.kts`
- `Android/my-profile/src/main/AndroidManifest.xml`
- `Android/my-profile/src/main/java/ru/home/sysdevsc/myprofile/...`
- `Android/my-profile/src/main/res/values/strings.xml`
- `Android/my-profile/src/test/java/ru/home/sysdevsc/myprofile/...`
- `Android/my-profile/src/androidTest/java/ru/home/sysdevsc/myprofile/...`
```

## Accepted decisions

Профиль реализуется как новая библиотечная единица Gradle Android с минимальным публичным Compose-контрактом и явными callbacks для logout/auth recovery. Repository скрывает источники профиля, истории и выхода; держатель состояния UI отдаёт неизменяемое состояние и принимает события. `:app` только создаёт зависимости, передаёт контекст сессии и компонует профильный контент в destination оболочки. `:app-shell` остаётся владельцем навигационной рамки и получает возможность отрисовать destination content без владения логикой профиля.

## Open questions

None.

## Risks

Основные риски: долгая постраничная загрузка истории может задержать включение действия «Мои интервью»; сетевой сбой logout может создать ложное ощущение выхода; выбранная краткая обратная связь должна быть ассистивно объявляемой на Android; корневая интеграция не должна перенести изменяемое состояние функции в `:app`; изменение content seam оболочки должно сохранить существующие проверки app-shell и выбранность вкладок.
