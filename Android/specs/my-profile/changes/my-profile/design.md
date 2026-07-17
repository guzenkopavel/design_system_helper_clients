# Design — my-profile / Android / my-profile

## Current context

Текущий Android graph содержит `:app`, `:app-shell` и `:auth`. `:app` уже выполняет корневую композицию между `AuthGate` и `AppShell`; `:app-shell` владеет нижней навигацией и временным content для `Profile`; `:auth` владеет auth flow, проверкой сессии, network client и secure storage, а это уже доставленная база авторизованного приложения. Доставленные документы базовой линии фиксируют поведение shell и auth, но отдельной возможности профиля, content seam для реального профиля, политики постраничной истории и действия logout в профиле пока нет; новое решение закрывает именно этот недостающий пользовательский путь.

## Proposed architecture and boundaries

Новая возможность создаётся как библиотечная единица Gradle Android `:my-profile`. Она содержит публичный Compose-контракт для профильного content, неизменяемое состояние UI, callbacks событий, ViewModel или держатель состояния, repository contract, default repository implementation, DTO для profile/history/logout и строковые ресурсы. `:app` компонует auth session, shell и контракт профиля; `:app-shell` предоставляет destination content seam или иной минимальный публичный slot; `:auth` остаётся baseline владельцем проверки сессии и recovery. Реализация профиля не переносится в application module или shell module.

## Modularity decision

- Outcome: isolated
- Capability triggers: independent-feature=yes; domain-data=yes; network=yes; persistence=no; reusable-ui=yes; consumers=1; independent-ownership=yes
- Physical boundaries: Proposed Gradle Android library module for profile capability isolation
- Public contracts and dependency direction: Публичный Compose contract принимает зависимости профиля, callback успешного logout, callback недействительной сессии и показывает content профильного destination; потребитель зависит от контракта, а repository sources скрыты внутри capability.
- App-shell responsibilities: entry-points, lifecycle, root-routing, dependency-wiring, platform-configuration, target-resources
- App-shell capability ownership: none
- Repository evidence: Android/settings.gradle.kts; Android/build.gradle.kts; Android/gradle/libs.versions.toml
- Rationale and trade-offs: Профиль объединяет самостоятельный UI, персональные server requests, постраничную историю, logout и privacy recovery; физическая граница защищает корневую композицию от состояния функции и делает проверки repository/state детерминированными. Цена — дополнительная настройка Gradle, но она оправдана владением и проверяемостью capability.
- Migration boundary and trigger: Переход начинается в этом пакете изменения до production implementation; если появятся дополнительные потребители или отдельная функция истории, публичный контракт расширяется через типизированную seam без переноса logic в корневую композицию.
- Over-modularization check: Одна физическая единица удерживает цельную profile capability вместе с UI, data policy и tests; split на отдельные data/ui units пока не нужен, потому что consumer один, implementation одна и дополнительный graph overhead не даёт новой visibility boundary.
- Boundary guard verdict: PASS

## Data and control flow

Пользователь выбирает profile destination в `AppShell`. Корневая композиция передаёт в профильный content зависимости сессии и callbacks. Держатель состояния профиля запускает загрузку профиля и счётчика истории: запрос профиля отдаёт email, запрос истории догружает pages до терминального состояния пагинации и публикует полный счётчик. UI отображает загрузку или готовые данные; действие «Мои интервью» отдаёт событие только при `count > 0` и показывает краткую обратную связь. Событие logout вызывает repository logout, блокирует повторную отправку и после успеха вызывает callback корня для сброса auth gate.

## Error and recovery model

Ошибка истории и состояние без сети не скрывают вкладку профиля и не блокируют logout; они переводят «Мои интервью» в недоступное состояние и показывают восстановимое сообщение пользователю, чтобы профиль оставался понятным. Сетевая ошибка logout не очищает персональные данные преждевременно и оставляет пользователя в профиле. Недействительная сессия при запросе профиля или истории вызывает восстановление авторизации и удаляет состояние профиля из композиции. Распространение отмены обязательно при уходе со вкладки, повторе logout и изменениях конфигурации; интерфейс не должен показывать устаревший email после смены состояния авторизации, потому что это нарушит приватность и доверие к экрану.

## Platform UX trace and decisions

Файл `platform-ux.md` готов и выбирает Material 3 как нативный адаптер для Android. Проект применяет MaterialTheme, семантические tonal roles, доступные on-colors, запасное soft-blue оформление, тихую поверхность, русские ресурсы, семантику недоступности, snackbar/toast-like feedback и проверку light/dark/increased contrast для визуального качества. M3 Expressive и Dynamic color не являются обязательными решениями; Dynamic color возможен только с доступным soft-blue fallback.

## Verification strategy

Plan должен создать проверки repository для profile/history/logout, детерминированные coroutine tests для пагинации и отмены, проверки ViewModel/state для состояний enabled/disabled/error/logout, Compose UI tests для semantics и обратной связи без навигации, проверки границы Gradle, consumer integration build и runtime UI evidence для внешнего вида Material 3. Отсутствие emulator фиксируется как неопределённый runtime-результат на verify, но не заменяет unit/state coverage.

## Applied engineering scopes

- application: Корневая композиция должна связать auth, shell, callbacks профиля и восстановление после logout, сохранив application module как владельца только entry point и wiring.
- compose: UI профиля использует state hoisting, неизменяемое состояние, однонаправленные события и lifecycle-aware collection в рамках найденной Compose конфигурации.
- concurrency: Пагинация, logout, отмена и retry требуют structured concurrency, propagation cancellation и явных состояний загрузки или ошибки для пользовательского пути.
- gradle: Новая библиотечная единица, settings include, dependencies и build tasks должны быть обнаружены и проверены через существующий Gradle wrapper без предположения fixed task set.
- localization: Русские labels, форматированная обратная связь со счётчиком и recovery messages должны находиться в resources профильной единицы с проверкой formatting и long text.
- module: Самостоятельная функция с UI, data и network policy изолируется в библиотечной единице Gradle Android с минимальным публичным контрактом.
- ui: Представление Material 3, accessibility semantics, TalkBack, font scaling, contrast, light/dark и состояния на emulator требуют сфокусированной проверки UI.

## Constraints

Не добавлять экран истории, детали интервью, редактирование профиля, кастомный аватар, аналитику, схему backend, изменения auth API, логику функции в `:app`, владение данными в `:app-shell` или обязательное оформление M3 Expressive; это прямо остаётся вне границ задачи и не должно попасть в план. Обработка session secret остаётся в существующей auth/session boundary; профильная единица получает только безопасную session-aware network возможность и callbacks для корневой композиции, а лишнее поведение остаётся вне scope.

## Integration points

`Android/settings.gradle.kts` добавляет `:my-profile`. `Android/my-profile/build.gradle.kts` использует Android library, Compose, lifecycle, coroutines, OkHttp/Moshi при необходимости и тестовые зависимости из version catalog. `Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt` связывает callback профиля со сбросом auth. `Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShell.kt` получает content seam для destination, не принимая владение состоянием профиля.

## Open questions

None.
