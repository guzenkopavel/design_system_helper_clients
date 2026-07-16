# task-002 — Реализовать selection contract и state tests

- Layer: domain
- Boundary owner: Владелец public state contract и deterministic transitions для app shell
- Engineering scopes: ["application", "module"]
- Depends on: task-001
- Status: done
- Evidence: evidence/reconciliation-20260716T120500Z-task-002-android-aligned.md
- Discovered command: rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 500 -- ./Android/gradlew -p Android --no-daemon :app-shell:compileDebugUnitTestKotlin --console=plain
- Estimate (ideal): 0.5–1.5 days
- Paths: proposed: Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShellDestination.kt; proposed: Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShellState.kt; proposed: Android/app-shell/src/test/java/ru/home/sysdevsc/appshell/AppShellStateTest.kt

## Goal

Определить минимальный public app-shell state contract и deterministic
transition logic для трёх утверждённых направлений.
Русское уточнение: задача описывает только состояние выбора и правила перехода
между утверждёнными разделами.

## Inline contract context

`REQ-2` требует first selection `Кейсы` и ровно один выбранный раздел в любой
момент. `REQ-3` и `AC-3` требуют выбора каждого утверждённого направления и
открытия его нейтральной поверхности. `AND-REQ-1` и `AND-AC-2` требуют
focused state tests на public module surface.

## Steps

Сначала написать focused RED unit tests для initial selection, repeated current
selection, каждого перехода destination и запрета impossible fourth state.
Затем реализовать только небольшой typed public contract, нужный downstream
Compose code. Application boundary остаётся чистой: Activity, Context,
Resources, storage, network, DI framework и Android lifecycle owner не входят
в держатель состояния. Module boundary остаётся видимой через public types, а
implementation helpers используют package-private/internal visibility там, где
это позволяет Kotlin. Public contract должен оставаться понятным для consumer
integration и будущей dependency graph inspection; app-shell wiring остаётся
вне этой задачи. Английские markers здесь являются точными проверками, а не
объяснительным текстом.
Русское уточнение: реализация должна оставаться маленькой, типизированной и
проверяемой без привязки к Android-контексту.

## Verification

Запустить узкий module unit test под watchdog после подтверждения обновлённого
task name. Provisional command: `rtk bash workflow/scripts/test-watchdog.sh
--max-seconds 300 --stall-seconds 60 --max-output-lines 1200 --
./Android/gradlew -p Android :app-shell:testDebugUnitTest --console=plain`.
Evidence должен показать application boundary, module boundary, module build,
public contract, consumer integration expectation, dependency graph direction
и app-shell wiring responsibility; это точный набор machine checks.
Русское уточнение: доказательства должны подтверждать границу модуля,
публичный контракт и направление зависимостей.
Дополнительное русское уточнение: проверка должна показать, что состояние
остаётся внутри отдельного модуля и не переносится в приложение.

## Expected result

Library раскрывает небольшой deterministic state contract, tests доказывают
утверждённые initial/changed selections, а неутверждённое состояние или
product content не появляются.

## Out of scope

Compose UI, resource labels, Activity wiring, persistence, analytics, emulator
run и visual styling в эту задачу не входят; эти поверхности остаются для
следующих задач.
Русское уточнение: ограничение защищает задачу от преждевременной работы над
интерфейсом и интеграцией приложения.
