# Verification — app shell / Android / app-shell

| Contract ID | Layer | Method | Evidence path | Status |
| --- | --- | --- | --- | --- |
| REQ-1 | integration | Compose navigation scenario проверяет фиксированный набор направлений и утверждённый порядок. | collected during Verify | pending |
| REQ-2 | presentation | Deterministic state scenario проверяет первый выбор и правило единственного выбранного раздела. | collected during Verify | pending |
| REQ-3 | presentation | Compose selection scenarios наблюдают нейтральную поверхность каждого утверждённого направления. | collected during Verify | pending |
| REQ-4 | presentation | Surface inspection подтверждает отсутствие вымышленных данных, загрузки, ошибок, аккаунта и профиля. | collected during Verify | pending |
| REQ-5 | accessibility | Semantics и appearance scenarios проверяют русские подписи, выбранное состояние, масштаб шрифта, contrast cues и светлое/тёмное поведение. | collected during Verify | pending |
| REQ-6 | integration | Contract trace и Android scenarios сравнивают фиксированные подписи, порядок, первый выбор и наблюдаемые переходы. | collected during Verify | pending |
| AC-1 | UI | Compose UI scenario наблюдает ровно три видимых navigation destinations в нужном порядке. | collected during Verify | pending |
| AC-2 | UI | Compose UI scenario наблюдает начальное выбранное направление и одну доступную selected semantic. | collected during Verify | pending |
| AC-3 | UI | Compose UI scenario выбирает каждое направление и наблюдает его нейтральную поверхность. | collected during Verify | pending |
| AC-4 | UI | Surface inspection scenario отклоняет content и state affordances вне утверждённого инкремента оболочки и будущих разделов. | collected during Verify | pending |
| AC-5 | accessibility | Semantics, font-scale и appearance checks наблюдают accessible labels и non-color selected cues для понятной выбранности каждого направления, доступного чтения и устойчивой навигации. | collected during Verify | pending |
| AND-REQ-1 | architecture | Gradle graph и public seam inspection проверяют физическое владение и направление композиции. | collected during Verify | pending |
| AND-REQ-2 | presentation | Material 3 UI и resource scenarios проверяют нативное доступное представление навигации. | collected during Verify | pending |
| AND-AC-1 | integration | Discovered Gradle build и dependency-graph inspection проверяют включение модульной границы и корневую композицию. | collected during Verify | pending |
| AND-AC-2 | tests | Deterministic state и Compose UI tests проверяют переходы состояния и selected semantics для утверждённых направлений. | collected during Verify | pending |
| AND-AC-3 | accessibility | Runtime или inspection evidence проверяет appearance, font scale, labels и semantic soft-blue fallback для доступного отображения, читаемых русских подписей и уверенного восприятия. | collected during Verify | pending |

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

## Native UX verification

READY-решения из `platform-ux.md` проверяются через Material 3 component
semantics, подписи из ресурсов, признаки выбранного состояния,
масштабирование шрифта, light/dark appearance, accessible on-colors и
soft-blue fallback. Обнаруженный emulator run дополняет эти проверки; без него
runtime-часть не заявляется, а evidence фиксирует точный доступный inspection
path.
Русское уточнение: проверка должна записать только реально полученные
доказательства и не считать недоступную среду успешной.

## Derived method matrix

Выбранный module scope требует проверки границы, сборки, публичного контракта,
consumer integration, dependency graph и app-shell wiring. Compose и UI
добавляют состояние, semantics, accessibility, design-system и runtime checks;
Gradle и localization добавляют discovered build и проверку владения
ресурсами.
Русское уточнение: матрица описывает, какие риски покрываются сборкой,
состоянием, ресурсами, доступностью и модульной границей.

## Unverified risks

На Propose не найден Android device или emulator. Runtime TalkBack,
increased-contrast rendering и lifecycle recreation поэтому требуют fresh
Verify evidence и не могут выводиться из статического package design.
Русское уточнение: эти риски остаются открытыми до свежего запуска Verify с
подходящей средой выполнения.
