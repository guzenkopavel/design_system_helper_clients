# Verification — app shell / Android / app-shell

| Contract ID | Layer | Method | Evidence path | Status |
| --- | --- | --- | --- | --- |
| REQ-1 | integration | Compose navigation scenario проверяет фиксированный набор направлений и утверждённый порядок. | evidence/verification-20260716T121500Z.md | PASS |
| REQ-2 | presentation | Deterministic state scenario проверяет первый выбор и правило единственного выбранного раздела. | evidence/verification-20260716T121500Z.md | PASS |
| REQ-3 | presentation | Compose selection scenarios наблюдают нейтральную поверхность каждого утверждённого направления. | evidence/verification-20260716T121500Z.md | PASS |
| REQ-4 | presentation | Surface inspection подтверждает отсутствие вымышленных данных, загрузки, ошибок, аккаунта и профиля. | evidence/verification-20260716T121500Z.md | PASS |
| REQ-5 | accessibility | Semantics и appearance scenarios проверяют русские подписи, выбранное состояние, масштаб шрифта, contrast cues и светлое/тёмное поведение. | evidence/verification-20260716T121500Z.md | PASS |
| REQ-6 | integration | Contract trace и Android scenarios сравнивают фиксированные подписи, порядок, первый выбор и наблюдаемые переходы. | evidence/verification-20260716T121500Z.md | PASS |
| AC-1 | UI | Compose UI scenario наблюдает ровно три видимых navigation destinations в нужном порядке. | evidence/verification-20260716T121500Z.md | PASS |
| AC-2 | UI | Compose UI scenario наблюдает начальное выбранное направление и одну доступную selected semantic. | evidence/verification-20260716T121500Z.md | PASS |
| AC-3 | UI | Compose UI scenario выбирает каждое направление и наблюдает его нейтральную поверхность. | evidence/verification-20260716T121500Z.md | PASS |
| AC-4 | UI | Surface inspection scenario отклоняет content и state affordances вне утверждённого инкремента оболочки и будущих разделов. | evidence/verification-20260716T121500Z.md | PASS |
| AC-5 | accessibility | Semantics, font-scale и appearance checks наблюдают accessible labels и non-color selected cues для понятной выбранности каждого направления, доступного чтения и устойчивой навигации. | evidence/verification-20260716T121500Z.md | PASS |
| AND-REQ-1 | architecture | Gradle graph и public seam inspection проверяют физическое владение и направление композиции. | evidence/verification-20260716T121500Z.md | PASS |
| AND-REQ-2 | presentation | Material 3 UI и resource scenarios проверяют нативное доступное представление навигации. | evidence/verification-20260716T121500Z.md | PASS |
| AND-AC-1 | integration | Discovered Gradle build и dependency-graph inspection проверяют включение модульной границы и корневую композицию. | evidence/verification-20260716T121500Z.md | PASS |
| AND-AC-2 | tests | Deterministic state и Compose UI tests проверяют переходы состояния и selected semantics для утверждённых направлений. | evidence/verification-20260716T121500Z.md | PASS |
| AND-AC-3 | accessibility | Runtime или inspection evidence проверяет appearance, font scale, labels и semantic soft-blue fallback для доступного отображения, читаемых русских подписей и уверенного восприятия. | evidence/verification-20260716T121500Z.md | PASS |

## Modularity verification

- Dependency graph: PASS
- Public API and visibility: PASS
- Module-level tests: PASS
- Consumer integration and build: PASS
- App-shell allowlist: PASS

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
