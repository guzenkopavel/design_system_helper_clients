# Verification — my-profile / iOS / my-profile

Свежая terminal-проверка выполнена после закрытия четырёх задач реализации с
timestamp `20260717T112843Z`. Проверка использует только актуальные исходники,
обновлённые task evidence и свежие verifier evidence этого запуска; прежние
черновые записи verifier-а не используются как terminal proof.

## Modularity verification

- Dependency graph: PASS
- Public API and visibility: PASS
- Module-level tests: PASS
- Consumer integration and build: PASS
- App-shell allowlist: PASS

Подробные наблюдения модульности находятся в
`evidence/verify-20260717T112843Z-boundaries.md` и
`evidence/verify-20260717T112843Z-tests.md`: package содержит профильную
доменную, сетевую, presentation и preview-session ответственность, а app target
оставляет за собой только composition, root routing и конфигурацию.

| Contract ID | Layer | Method | Evidence path | Status |
|---|---|---|---|---|
| REQ-1 | общий контракт | Runtime-сценарий профиля и инспекция accessibility identifier подтверждают символ, email и состояние вкладки профиля. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| REQ-2 | общий контракт | Package tests проверяют полную догрузку истории интервью до окончания страниц. | evidence/verify-20260717T112843Z-tests.md | PASS |
| REQ-3 | общий контракт | Package tests и UI tests подтверждают доступное действие при положительном счётчике интервью. | evidence/verify-20260717T112843Z-tests.md | PASS |
| REQ-4 | общий контракт | UI tests подтверждают сообщение `Интервью: 3` без навигационного перехода. | evidence/verify-20260717T112843Z-tests.md | PASS |
| REQ-5 | общий контракт | UI tests подтверждают видимое недоступное действие при пустой истории. | evidence/verify-20260717T112843Z-tests.md | PASS |
| REQ-6 | общий контракт | UI tests подтверждают выход к пустому вводу email и очистку прошлого профиля. | evidence/verify-20260717T112843Z-tests.md | PASS |
| REQ-7 | общий контракт | Package tests и UI tests подтверждают ошибку истории, недействительную сессию и сбой выхода. | evidence/verify-20260717T112843Z-tests.md | PASS |
| REQ-8 | общий контракт | Сверка общей READY-спеки, client readiness и iOS runtime показывает отсутствие iOS-ветвления от shared product contract. | evidence/verify-20260717T112843Z-cross-client.md | PASS |
| REQ-9 | общий контракт | Инспекция SwiftUI accessibility и UI automation по русским labels подтверждают доступную семантику email, действий и состояний. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| REQ-10 | общий контракт | Отдельные simulator runs подтверждают light, dark, increased contrast и максимальный Dynamic Type для профильной поверхности. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-1 | общая приёмка | UI automation наблюдает email, `my-profile.symbol`, действия и профильное содержимое на активной вкладке. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-2 | общая приёмка | Package tests проверяют последовательную пагинацию и остановку на `hasMore = false`. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-3 | общая приёмка | Package tests и UI tests подтверждают доступность интервью-действия при `count > 0`. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-4 | общая приёмка | UI test подтверждает точное русское сообщение `Интервью: 3`. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-5 | общая приёмка | UI test сохраняет профильную вкладку и подтверждает отсутствие push/navigation stack после нажатия. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-6 | общая приёмка | UI test подтверждает disabled-состояние интервью-действия при пустой истории. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-7 | общая приёмка | UI test подтверждает возврат к пустому email input после выхода. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-8 | общая приёмка | UI-тест подтверждает отсутствие старого email после выхода. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-9 | общая приёмка | UI- и state-тесты подтверждают ошибку истории с сохранённым выходом и заблокированным интервью-действием. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-10 | общая приёмка | UI-тесты подтверждают недействительную сессию с возвратом в авторизацию и без прошлого email. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-11 | общая приёмка | Тесты пакета подтверждают сбой выхода без ложного завершения сессии и без потери профиля. | evidence/verify-20260717T112843Z-tests.md | PASS |
| AC-12 | общая приёмка | Готовность общего продуктового контракта зафиксирована для обоих клиентов, а iOS-реализация не вводит собственную поведенческую развилку. | evidence/verify-20260717T112843Z-cross-client.md | PASS |
| AC-13 | общая приёмка | SwiftUI-семантика доступности и UI-автоматизация по видимым подписям подтверждают смысл email и действий. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-14 | общая приёмка | Тесты представления и инспекция исходников подтверждают объявления занятости, причину недоступности и ошибочные состояния без цветовой зависимости. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-15 | общая приёмка | Запуск симулятора с `accessibility-extra-extra-extra-large` подтверждает профильную поверхность без обрезания проверяемых элементов. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-16 | общая приёмка | Отдельные запуски симулятора подтверждают профильную поверхность в светлом и тёмном оформлении. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-17 | общая приёмка | Запуск симулятора с повышенным контрастом подтверждает читаемые состояния и нецветовые признаки. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| AC-18 | общая приёмка | Runtime-наблюдения и тесты представления подтверждают загрузку, содержимое, пустую историю, ошибку, недействительную сессию и выход без зависимости только от цвета. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| IOS-REQ-1 | платформенный контракт | Инспекция границ подтверждает, что app target только связывает `MyProfileFeatureFactory`, а профильные сценарии живут в Swift package. | evidence/verify-20260717T112843Z-boundaries.md | PASS |
| IOS-REQ-2 | платформенный контракт | State-тесты и тесты пакета подтверждают контракты auth/session request, историю и mapping ошибок. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-REQ-3 | платформенный контракт | Тесты пакета и UI-тесты подтверждают состояние представления и все профильные fixture-сценарии. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-REQ-4 | платформенный контракт | UI-тесты подтверждают восстановление после недействительной сессии, выход и пути сбоя. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-REQ-5 | платформенный контракт | Нативная runtime-матрица подтверждает оформление, доступность, адаптацию устройства и obligations для fallback. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| IOS-REQ-6 | платформенный контракт | Тесты пакета подтверждают единственную активную загрузку, отмену и поведение пагинации. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-AC-1 | платформенная приёмка | Тесты Swift package и полный набор Xcode подтверждают сборку физического пакета и интеграцию потребителя. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-AC-2 | платформенная приёмка | App-shell allowlist подтверждён отсутствием профильной заглушки и профильных request cases в app target. | evidence/verify-20260717T112843Z-boundaries.md | PASS |
| IOS-AC-3 | платформенная приёмка | State-тесты подтверждают request boundaries и использование session client, принадлежащего auth-слою. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-AC-4 | платформенная приёмка | Тесты пакета подтверждают mapping ошибок, недействительную сессию и состояния восстановления. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-AC-5 | платформенная приёмка | UI-тесты подтверждают содержимое профиля, символ, действия и обратную связь по счётчику. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| IOS-AC-6 | платформенная приёмка | UI-тесты подтверждают выход к пустому полю email. | evidence/verify-20260717T112843Z-tests.md | PASS |
| IOS-AC-7 | платформенная приёмка | Все нативные obligations имеют отдельные PASS-записи наблюдений с underlying evidence. | evidence/verify-20260717T112843Z-native-runtime.md | PASS |
| IOS-AC-8 | платформенная приёмка | Тесты пакета подтверждают пагинацию, защиту от повторной загрузки и отмену. | evidence/verify-20260717T112843Z-tests.md | PASS |

## Revalidated engineering scopes and exact verify rules

Области остаются `application`, `concurrency`, `localization`, `networking`,
`package`, `ui`. Verify использует неизменный `plan/rule-selection.json`,
общую модульность v1, платформенное UX-дополнение и выбранные iOS-правила из
`meta.json`; новые области или исключения во время проверки не добавлялись.

## Derived method matrix

- `swift test --package-path iOS/MyProfileFeature` подтвердил пакетную сеть,
  пагинацию, mapping ошибок, отмену, единственную активную загрузку и ветки
  представления для прозрачности, движения и резервного символа.
- Фокусный `AppShellStateTests` подтвердил композицию потребителя: app target не
  владеет профильной session-заглушкой, не объявляет profile/history/logout
  request cases и получает preview session client из feature package.
- Фокусные UI-запуски профиля подтвердили содержимое, пустую историю, ошибку
  истории, недействительную сессию, выход и сбой выхода.
- Полный набор `SysDevScen` на iPhone подтвердил отсутствие регрессии в
  app shell, авторизации, интервью и профильных потоках.
- Отдельные запуски настроек симулятора подтвердили светлое и тёмное
  оформление, повышенный контраст, максимальный Dynamic Type и адаптацию на
  iPad mini.

## Native UX verification

Нативная матрица закрыта комбинацией runtime-наблюдений, тестов представления
пакета и инспекции исходников. UI-автоматизация работала через видимые русские
подписи и identifier `my-profile.symbol`, что одновременно проверяет доступные
имена основных элементов. Отдельные настройки симулятора подтвердили оформление
и измерения доступности на iPhone 17; iPad mini подтвердил адаптацию формы
плавающей панели вкладок через резервный поиск по `label` и `identifier`.
Уменьшение движения и резервная доступность подтверждены тестами представления и
условными SwiftUI-ветками, потому что это детерминированное evidence для условий
среды.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | evidence/native-appearance-20260717T112843Z.json | PASS |
| NATIVE-LIGHT | evidence/native-light-20260717T112843Z.json | PASS |
| NATIVE-DARK | evidence/native-dark-20260717T112843Z.json | PASS |
| NATIVE-INCREASED-CONTRAST | evidence/native-increased-contrast-20260717T112843Z.json | PASS |
| NATIVE-ASSISTIVE-SEMANTICS | evidence/native-assistive-semantics-20260717T112843Z.json | PASS |
| NATIVE-TEXT-SCALING | evidence/native-text-scaling-20260717T112843Z.json | PASS |
| NATIVE-MOTION | evidence/native-motion-20260717T112843Z.json | PASS |
| NATIVE-DEVICE-ADAPTATION | evidence/native-device-adaptation-20260717T112843Z.json | PASS |
| NATIVE-AVAILABILITY-FALLBACK | evidence/native-availability-fallback-20260717T112843Z.json | PASS |

## Unverified risks and blockers

Terminal-блокеры отсутствуют. Живые destructive backend credentials не
использовались: проверка намеренно опирается на детерминированные session
clients и simulator fixtures, чтобы runtime evidence было воспроизводимым и не
зависело от внешнего состояния сервера.
