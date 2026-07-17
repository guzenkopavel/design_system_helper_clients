# План — my-profile / Android / my-profile

## Planning frame

Реализовать утверждённую вкладку профиля как изолированную библиотечную возможность `:my-profile`. Новый модуль владеет состоянием профиля, загрузкой текущей почты, полной постраничной историей интервью, выходом из сессии, русскими ресурсами и экраном на `Material 3` / `Compose`. `:app` остаётся владельцем только входной точки, жизненного цикла, корневой маршрутизации, связывания зависимостей, платформенной конфигурации и целевых ресурсов; `:app-shell` остаётся навигационной рамкой и получает минимальный слот содержимого для вкладки профиля без владения данными или состоянием профиля.

## Revalidated engineering scopes and exact rules

- Selection snapshot: `plan/rule-selection.json`
- Selection evidence: финальные области `["application","compose","concurrency","gradle","localization","module","ui"]` подтверждены `implementation-spec.md`, `design.md`, `platform-ux.md`, `Android/settings.gradle.kts`, `Android/app/build.gradle.kts`, `Android/app-shell/build.gradle.kts`, `Android/auth/build.gradle.kts`, `Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShell.kt` и `Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt`. В проекте уже обнаружены `Compose`, `Material 3`, корутины, `OkHttp`, `Moshi`, `:app`, `:app-shell`, `:auth` и wrapper сборки; отдельной возможности профиля, слота содержимого и репозитория профиля пока нет.

## Assumptions

Публичный профильный контракт получает сетевую возможность, связанную с сессией, и обратные вызовы от корневой композиции, а не читает защищённое хранилище авторизации напрямую. Пути запросов следуют общему контракту: `GET /api/profile`, `GET /api/interviews/history` и `POST /api/auth/logout`; конкретная сериализация уточняется реализацией через существующие зависимости `OkHttp` и `Moshi`. Если эмулятор или устройство недоступны на проверке, runtime-доказательство получает `UNKNOWN`, а покрытие unit/state не превращается в runtime `PASS`.

## DAG

`task-001` не имеет зависимостей и создаёт границу `:my-profile` в сборке. `task-002` зависит от `task-001` и реализует политику данных профиля с полной пагинацией и выходом. `task-003` зависит от `task-002` и создаёт представление `Compose`, внешний вид `Material 3`, локализацию и доступность. `task-004` зависит от `task-003` и подключает профильный слот содержимого в оболочке и корневую композицию приложения. `task-005` зависит от `task-004` и закрывает сфокусированные проверки модуля, потребителя, интерфейса и runtime. Такой граф идёт от физической границы к данным, представлению, интеграционному связыванию и проверке без скрытого владения production-кодом.

## Tasks

`task-001` покрывает обнаружение `Gradle task`, подключение в settings, `module build`, `public contract`, `dependency graph` и начальную границу видимости. `task-002` покрывает репозиторий, транспортные модели, завершение пагинации, сопоставление недействительной сессии, политику выхода, `cancellation` и детерминированные unit-проверки. `task-003` покрывает состояние профиля в `Compose`, `Material 3`, `platform-ux.md`, `light/dark`, `accessible on-colors`, решение по `dynamic color`, `soft-blue fallback`, локализацию, семантику и увеличение текста. `task-004` покрывает `application boundary`, слот содержимого оболочки, `app-shell wiring`, обратные вызовы восстановления авторизации и `consumer integration`. `task-005` покрывает сфокусированные команды проверки, evidence для `emulator`, `accessibility` и `design-system`, `module build`, `consumer integration`, `dependency graph` и поведение без навигации.

## Estimates and multipliers

Каждая задача ограничена двумя идеальными днями. Увеличивающие факторы: новый библиотечный модуль с репозиторием, сетью и интерфейсом внутри одной возможности, отсутствие готового профильного шва в оболочке, необходимость полной пагинации перед публикацией счётчика, восстановление после выхода и runtime-проверки внешнего вида `Material 3`. Снижающие факторы: уже есть wrapper сборки, каталог версий, `Compose`, `Material 3`, корутины, `OkHttp` / `Moshi`, baseline авторизации и доставленная граница оболочки.

## Verification strategy

Для нового наблюдаемого поведения применять `TDD`: сначала красная проверка на репозитории, состоянии, интерфейсе или отсутствующем артефакте, затем минимальный зелёный результат, затем сфокусированная регрессия. Обнаруженные команды до материализации: `./gradlew tasks --all --console=plain`, `./gradlew :app:testDebugUnitTest --console=plain`, `./gradlew :app:lintDebug --console=plain`, `./gradlew :app:assembleDebug --console=plain`, `./gradlew :app:connectedDebugAndroidTest --console=plain`. Команды `:my-profile:testDebugUnitTest`, `:my-profile:lintDebug`, `:my-profile:assembleDebug`, `:my-profile:connectedDebugAndroidTest` являются предварительными до `task-001`; после включения модуля они должны быть подтверждены повторным обнаружением задач сборки.

## Test and performance budgets

Команды unit/state запускать через `workflow/scripts/test-watchdog.sh` с `--max-seconds 300 --stall-seconds 60 --max-output-lines 1200`. Команды build/lint запускать с `--max-seconds 420 --stall-seconds 90 --max-output-lines 2000`. Команды runtime UI запускать с `--max-seconds 600 --stall-seconds 120 --max-output-lines 2500` и только при обнаруженном эмуляторе или устройстве. Отдельный `performance SLA` не заявляется; бюджет производительности ограничен отсутствием сетевого или файлового I/O на главном потоке, bounded pagination loop, propagation of cancellation и отсутствием повторной отправки выхода.

## Checkpoints

Перед реализацией нужно подтвердить, что writable `Paths` каждой задачи не пересекаются и не входят в protected roots. После `task-001` обновить обнаружение задач сборки и заменить предварительные команды модуля на подтверждённое evidence. После `task-003` не принимать интерфейс без проверок `platform-ux.md`, `Material 3`, `light/dark`, `accessible on-colors`, решения по `dynamic color` и `soft-blue fallback`. Перед terminal verify выполнить сфокусированные проверки модуля, проверки потребителя приложения, lint/build и runtime UI evidence либо честный `UNKNOWN`.

## Risks

Главный риск — случайно перенести логику профиля в `:app` или `:app-shell`; задачи фиксируют владельца границы и владение capability в оболочке как `none`. Второй риск — считать первую страницу истории полным количеством; задача репозитория требует терминальную пагинацию. Третий риск — недоступность эмулятора или `TalkBack` runtime; это ограничивает только runtime evidence, но не отменяет обязательства module/state/UI проверок.
