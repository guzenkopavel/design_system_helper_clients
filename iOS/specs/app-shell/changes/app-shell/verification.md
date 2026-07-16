# iOS verification — app shell

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

## Native UX verification

После READY `platform-ux.md` работа в симуляторе проверит семантику стандартных
controls, порядок и состояние `VoiceOver`, `Dynamic Type`, light/dark appearance,
increased contrast, `Reduce Transparency` и `Reduce Motion`. Device, runtime,
scheme, launch/reset policy и diagnostics будут обнаружены, а не предположены.

## Traceability

| Contract ID | Layer | Method | Expected evidence | Status |
|---|---|---|---|---|
| REQ-1 | shared intake | Сверить утверждённый общий договор со сценарием корневой композиции iOS | evidence/shared-intake-review.md | pending |
| REQ-2 | shared intake | Запустить первый экран из сброшенного состояния приложения | evidence/first-launch-scenario.md | pending |
| REQ-3 | shared intake | Пройти каждый утверждённый выбор корневого раздела через стандартные controls | evidence/root-routing-scenario.md | pending |
| REQ-4 | shared intake | Проверить заменённую поверхность на отсутствие исключённого шаблона и интеграции | evidence/scope-inspection.md | pending |
| REQ-5 | shared intake | Проверить подписи, состояние выбора и условия accessibility/appearance | evidence/accessibility-appearance.md | pending |
| REQ-6 | shared intake | Сравнить iOS-маппинг сценария с общими ссылками на parity | evidence/parity-mapping.md | pending |
| AC-1 | shared acceptance | Подтвердить утверждённый сценарий запуска и навигации на доступном simulator | evidence/ac-1-simulator.md | pending |
| AC-2 | shared acceptance | Подтвердить начальное семантическое состояние выбора через нативную поверхность | evidence/ac-2-accessibility.md | pending |
| AC-3 | shared acceptance | Подтвердить каждый исход маршрутизации и перенос выбранного состояния | evidence/ac-3-ui-flow.md | pending |
| AC-4 | shared acceptance | Проверить видимую корневую поверхность относительно утверждённых исключений | evidence/ac-4-scope.md | pending |
| AC-5 | shared acceptance | Выполнить сфокусированные assistive и appearance проверки для утверждённого результата accessibility | evidence/ac-5-accessibility.md | pending |
| IOS-REQ-1 | architecture | Проверить точку входа, корневую маршрутизацию и владение target по найденному графу проекта | evidence/ios-root-boundary.md | pending |
| IOS-REQ-2 | presentation | Запустить accessibility-сценарий нативных controls после READY UX decisions | evidence/ios-native-semantics.md | pending |
| IOS-REQ-3 | presentation | Проверить source и runtime surface на удаление взаимодействий технического шаблона | evidence/ios-template-removal.md | pending |
| IOS-AC-1 | integration | Запустить app и проверить реализованную composition boundary | evidence/ios-root-launch.md | pending |
| IOS-AC-2 | UI | Пройти нативный semantic path и проверить состояние VoiceOver | evidence/ios-semantic-ui.md | pending |
| IOS-AC-3 | regression | Проверить заменённую поверхность на прежние Core Data interactions и исключённые boundaries | evidence/ios-template-regression.md | pending |
