# iOS verification — app shell

## Modularity verification

- Dependency graph: PASS
- Public API and visibility: PASS
- Module-level tests: PASS
- Consumer integration and build: PASS
- App-shell allowlist: PASS

Доказательства modularity checks находятся в `evidence/ios-root-boundary.md`,
`evidence/ios-template-regression.md`, `evidence/ios-root-launch.md` и
`evidence/scope-inspection.md`.

## Native UX verification

После READY `platform-ux.md` проверка выполнена на simulator `iPhone 17 Pro`
с iOS 26.5. Свежие UI tests подтвердили семантику стандартных controls,
порядок и selected state. Runtime screenshots во временных файлах подтвердили
светлый режим, тёмный режим, повышенный контраст и Dynamic Type. Для
`Reduce Transparency` и `Reduce Motion` применён системный fallback: в source
отсутствуют самодельный material, blur, glass effect, явная animation и
transition.

## Traceability

| Contract ID | Layer | Method | Expected evidence | Status |
|---|---|---|---|---|
| REQ-1 | shared intake | Сверить утверждённый общий договор со сценарием корневой композиции iOS | evidence/shared-intake-review.md | PASS |
| REQ-2 | shared intake | Запустить первый экран из сброшенного состояния приложения | evidence/first-launch-scenario.md | PASS |
| REQ-3 | shared intake | Пройти каждый утверждённый выбор корневого раздела через стандартные controls | evidence/root-routing-scenario.md | PASS |
| REQ-4 | shared intake | Проверить заменённую поверхность на отсутствие исключённого шаблона и интеграции | evidence/scope-inspection.md | PASS |
| REQ-5 | shared intake | Проверить подписи, состояние выбора и условия accessibility/appearance | evidence/accessibility-appearance.md | PASS |
| REQ-6 | shared intake | Сравнить iOS-маппинг сценария с общими ссылками на parity | evidence/parity-mapping.md | PASS |
| AC-1 | shared acceptance | Подтвердить утверждённый сценарий запуска и навигации на доступном simulator | evidence/ac-1-simulator.md | PASS |
| AC-2 | shared acceptance | Подтвердить начальное семантическое состояние выбора через нативную поверхность | evidence/ac-2-accessibility.md | PASS |
| AC-3 | shared acceptance | Подтвердить каждый исход маршрутизации и перенос выбранного состояния | evidence/ac-3-ui-flow.md | PASS |
| AC-4 | shared acceptance | Проверить видимую корневую поверхность относительно утверждённых исключений | evidence/ac-4-scope.md | PASS |
| AC-5 | shared acceptance | Выполнить сфокусированные assistive и appearance проверки для утверждённого результата accessibility | evidence/ac-5-accessibility.md | PASS |
| IOS-REQ-1 | architecture | Проверить точку входа, корневую маршрутизацию и владение target по найденному графу проекта | evidence/ios-root-boundary.md | PASS |
| IOS-REQ-2 | presentation | Запустить accessibility-сценарий нативных controls после READY UX decisions | evidence/ios-native-semantics.md | PASS |
| IOS-REQ-3 | presentation | Проверить source и runtime surface на удаление взаимодействий технического шаблона | evidence/ios-template-removal.md | PASS |
| IOS-AC-1 | integration | Запустить app и проверить реализованную composition boundary | evidence/ios-root-launch.md | PASS |
| IOS-AC-2 | UI | Пройти нативный semantic path и проверить состояние VoiceOver | evidence/ios-semantic-ui.md | PASS |
| IOS-AC-3 | regression | Проверить заменённую поверхность на прежние Core Data interactions и исключённые boundaries | evidence/ios-template-regression.md | PASS |
