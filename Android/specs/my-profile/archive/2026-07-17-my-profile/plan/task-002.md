# task-002 — Реализовать репозиторий и состояние профиля

- Layer: data
- Boundary owner: Владелец политики данных и конкурентности внутри возможности профиля
- Engineering scopes: ["concurrency"]
- Depends on: task-001
- Status: done
- Evidence: evidence/task-002.md
- Estimate (ideal): 1-2 days
- Read-only context: ["Android/auth/src/main/java/ru/home/sysdevsc/auth/data/DefaultAuthApiService.kt","Android/auth/src/main/java/ru/home/sysdevsc/auth/data/SessionRepository.kt","Android/specs/my-profile/changes/my-profile/design.md","Android/specs/my-profile/changes/my-profile/implementation-spec.md","specs/product/my-profile/spec.md"]
- Paths: proposed: Android/my-profile/src/main/java/ru/home/sysdevsc/myprofile/data; proposed: Android/my-profile/src/main/java/ru/home/sysdevsc/myprofile/model; proposed: Android/my-profile/src/test/java/ru/home/sysdevsc/myprofile/data; proposed: Android/my-profile/src/test/java/ru/home/sysdevsc/myprofile/model

## Goal

Сформировать границу репозитория профиля: текущая почта, полная постраничная история интервью, доступность действия «Мои интервью», выход, восстановление недействительной сессии и загрузка с учётом отмены без владения интерфейсом.

## Inline contract context

`AND-REQ-3` требует загрузку текущего профиля без раскрытия технического `id` в состоянии интерфейса. `AND-REQ-4` требует догружать страницы истории до завершения пагинации. `AND-REQ-7` требует выход с блокировкой повторной отправки и обратным вызовом успешного завершения сессии. `AND-REQ-9` и `AND-REQ-10` требуют восстановимые состояния истории или offline и очистку при недействительной сессии. `AND-AC-4`, `AND-AC-5`, `AND-AC-6`, `AND-AC-8`, `AND-AC-9` и `AND-AC-10` фиксируют проверяемые исходы этих правил.

## Implementation deliverables

- Появится контракт репозитория профиля и default implementation, которые запрашивают текущую почту профиля, догружают все страницы истории до терминального состояния пагинации и публикуют типизированное состояние без технического идентификатора пользователя.
- Детерминированные coroutine tests подтвердят `cancellation`, загрузку с учётом жизненного цикла, очистку недействительной сессии, успешный выход, сбой выхода и отсутствие доступного действия до полного известного счётчика истории.

## Steps

Описать модели профиля, страницы истории, результата выхода и исхода недействительной сессии внутри `:my-profile`. Реализовать репозиторий через constructor injection и сетевую зависимость, связанную с сессией, не читая secure storage напрямую и не добавляя DI framework. Написать красные проверки для многостраничной истории, нулевого счётчика, неизвестного счётчика, ошибки истории, offline, недействительной сессии, успешного выхода, сетевого сбоя выхода и `cancellation propagation`. Реализация должна использовать structured concurrency, явные границы диспетчера там, где выполняется I/O, и не публиковать первую страницу как полный count при наличии следующей страницы.

## Verification

- Discovered command: `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 1200 -- ./gradlew :my-profile:testDebugUnitTest --console=plain`
- Watchdog max/stall/output budget for nontrivial checks: `300s / 60s / 1200 lines`; команда provisional до подтверждения `task-001`, затем становится точной discovered command.
- Applicable rule/check mapping: детерминированные coroutine tests покрывают `cancellation` и `lifecycle`; проверки репозитория покрывают завершение пагинации, типизированные ошибки, блокировку повторного выхода и отсутствие сетевого I/O на главном потоке.

## Expected result

Слой данных профиля выдаёт неизменяемое состояние для представления, корректно различает загрузку, готовность, пустую историю, ошибку, offline, недействительную сессию и процесс выхода, а проверки доказывают полную пагинацию и propagation of cancellation без владения UI или application.

## Out of scope

Разметка `Compose`, оформление `Material 3`, строковые ресурсы, слот destination в оболочке, связывание `MainActivity`, запуск эмулятора и пользовательский экран истории не входят в эту задачу.
