# task-003 — Собрать Material 3 shell UI и resources

- Layer: presentation
- Boundary owner: Владелец Material 3 composable, semantics и resource labels для app shell
- Engineering scopes: ["compose", "localization", "ui"]
- Depends on: task-002
- Status: pending
- Evidence: none
- Estimate (ideal): 1–2 days
- Paths: proposed: Android/app-shell/src/main/java/ru/home/sysdevsc/appshell/AppShell.kt; proposed: Android/app-shell/src/main/res/values/strings.xml; proposed: Android/app-shell/src/androidTest/java/ru/home/sysdevsc/appshell/AppShellTest.kt; proposed: Android/app-shell/src/main/res/values/colors.xml

## Goal

Отрисовать утверждённую оболочку с Material 3 navigation, русскими подписями
из ресурсов, нейтральными поверхностями, selected semantics и soft-blue
fallback decisions из `platform-ux.md`.

## Inline contract context

`REQ-1`, `REQ-4`, `REQ-5`, `REQ-6`, `AC-1`, `AC-4` и `AC-5` требуют ровно три
утверждённых направления, отсутствие fabricated content, accessible selected
state, consistent Android parity и readable appearance behavior.
`AND-REQ-2`, `AND-AC-2` и `AND-AC-3` требуют native accessible presentation на
Material 3.
Русское уточнение: задача связывает утверждённые продуктовые ограничения с
доступным нативным отображением на Android.

## Steps

До implementation написать Compose UI tests для трёх подписей в порядке,
initial selected semantics, выбора каждого направления, ровно одного selected
item и отсутствия loading, error, account или data affordances. Реализовать
state-hoisted composable на Material 3 и MaterialTheme, сохраняя Compose state
однонаправленным и стабильным. Visible и accessible Russian labels хранить в
resources, а localization fallback проверять с учётом длинного текста.
Выполнить design-system checks через semantic color roles, typography, shapes
и non-color selected cues. Следовать `platform-ux.md`: Material 3 выбран,
light/dark appearance должен раскрывать accessible on-colors, dynamic color
остаётся выключенным без Android 12+ repository SDK/dependency/product
evidence, а soft-blue fallback остаётся authoritative. Emulator accessibility
coverage добавляется, когда обнаружен runtime.
Русское уточнение: интерфейс должен быть проверяемым, ресурсным и доступным без
включения неподтверждённых визуальных возможностей.

## Verification

Запустить focused Compose scenarios на обнаруженном framework. Provisional
runtime command после module wiring: `rtk bash
workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120
--max-output-lines 2500 -- ./Android/gradlew -p Android
:app-shell:connectedDebugAndroidTest --console=plain`. Если emulator или
device недоступен, runtime-only TalkBack evidence записывается как UNKNOWN, а
available static/host checks всё равно выполняются. Evidence должен включать
Compose state, localization, emulator, accessibility, design-system,
platform-ux.md, Material 3, light/dark, accessible on-colors, dynamic color и
soft-blue fallback checks; эти markers нужны для машинной проверки задачи.
Русское уточнение: проверка должна различать доступные host/static checks и
runtime evidence, если устройство или эмулятор не найдены.
Дополнительное русское уточнение: результат проверки должен быть честным,
повторяемым и связанным с пользовательской доступностью оболочки.

## Expected result

Library composable показывает утверждённую Android shell, использует
resource-backed Russian labels, сохраняет accessible selected state не только
через color и остаётся согласованным с Material 3 decisions из
`platform-ux.md`.
Русское уточнение: результат должен сохранить понятную выбранность, русские
подписи и нативный визуальный baseline.

## Out of scope

`:app` consumer wiring, persistence, Dynamic color enablement, M3 Expressive
adoption, network/data state и product content для трёх разделов в эту задачу
не входят.
Русское уточнение: задача не добавляет данные, сеть, персонализацию или
реальное содержимое будущих разделов.
Дополнительное русское уточнение: задача ограничена визуальной оболочкой и не
создаёт новые функции, данные или внешние зависимости.
