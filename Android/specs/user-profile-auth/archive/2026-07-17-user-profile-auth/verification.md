# Verification — user-profile-auth / Android / user-profile-auth

| Contract ID | Layer | Method | Evidence path | Status |
|---|---|---|---|---|
| REQ-1 | integration | Проверка корневой маршрутизации подтверждает, что без сессии оболочка недоступна. | evidence/verification-20260717.md | PASS |
| REQ-2 | integration | Сценарии проверки флоу подтверждают ветвление по почте и возврат к первому шагу. | evidence/verification-20260717.md | PASS |
| REQ-3 | integration | Сценарии успешного входа и регистрации подтверждают переход в оболочку с разделом «Кейсы». | evidence/verification-20260717.md | PASS |
| REQ-4 | integration | Проверка перезапуска подтверждает сохранение и восстановление сессии. | evidence/verification-20260717.md | PASS |
| REQ-5 | integration | Сценарии ошибок подтверждают различимость и восстановимость всех наблюдаемых состояний. | evidence/verification-20260717.md | PASS |
| REQ-6 | integration | Сценарии истечения сессии подтверждают возврат на экран входа и очистку данных. | evidence/verification-20260717.md | PASS |
| REQ-7 | security | Проверка хранилища и конфигурации сети подтверждает защищённое хранение и передачу. | evidence/verification-20260717.md | PASS |
| REQ-8 | accessibility | Проверка доступных технологий, масштабирование и смена оформления подтверждают доступность. | evidence/verification-20260717.md | PASS |
| REQ-9 | integration | Сценарий сравнения с iOS подтверждает идентичные шаги, тексты и правила гейтинга. | evidence/verification-20260717.md | PASS |
| AC-1 | UI | Сценарий запуска без сессии подтверждает экран входа и отсутствие навигации. | evidence/verification-20260717.md | PASS |
| AC-2 | UI | Сценарий ввода существующей почты подтверждает заголовок «Вход». | evidence/verification-20260717.md | PASS |
| AC-3 | UI | Сценарий ввода новой почты подтверждает заголовок «Регистрация». | evidence/verification-20260717.md | PASS |
| AC-4 | UI | Сценарий возврата подтверждает сохранение введённой почты. | evidence/verification-20260717.md | PASS |
| AC-5 | UI | Сценарий успешного входа подтверждает оболочку с разделом «Кейсы». | evidence/verification-20260717.md | PASS |
| AC-6 | UI | Сценарий успешной регистрации подтверждает оболочку с разделом «Кейсы». | evidence/verification-20260717.md | PASS |
| AC-7 | UI | Сценарий перезапуска подтверждает оболочку без экрана входа. | evidence/verification-20260717.md | PASS |
| AC-8 | UI | Сценарий неверного пароля подтверждает ошибку и очистку поля. | evidence/verification-20260717.md | PASS |
| AC-9 | UI | Сценарий пустого поля подтверждает объяснение без отправки запроса. | evidence/verification-20260717.md | PASS |
| AC-10 | tests | Тест локальной валидации почты подтверждает отклонение до запроса. | evidence/verification-20260717.md | PASS |
| AC-11 | tests | Тест локальной валидации пароля подтверждает отклонение короткого пароля. | evidence/verification-20260717.md | PASS |
| AC-12 | UI | Сценарий ограничения попыток подтверждает состояние с указанием времени. | evidence/verification-20260717.md | PASS |
| AC-13 | UI | Сценарий занятой почты подтверждает объяснение о существовании аккаунта. | evidence/verification-20260717.md | PASS |
| AC-14 | tests | Сценарий отсутствия сети подтверждает восстановимое состояние. | evidence/verification-20260717.md | PASS |
| AC-15 | UI | Сценарий истечения сессии подтверждает возврат на вход с объяснением. | evidence/verification-20260717.md | PASS |
| AC-16 | tests | Проверка хранилища подтверждает очистку недействительного секрета. | evidence/verification-20260717.md | PASS |
| AC-17 | security | Проверка хранилища подтверждает отсутствие пароля. | evidence/verification-20260717.md | PASS |
| AC-18 | security | Инспекция хранилища подтверждает изоляцию сессионных данных. | evidence/verification-20260717.md | PASS |
| AC-19 | accessibility | Доступные технологии подтверждают имена полей, действий и объявление ошибок. | evidence/verification-20260717.md | PASS |
| AC-20 | accessibility | Проверка фокуса подтверждает переход к началу нового шага. | evidence/verification-20260717.md | PASS |
| AC-21 | accessibility | Визуальная проверка подтверждает различимость без опоры на цвет. | evidence/verification-20260717.md | PASS |
| AC-22 | accessibility | Проверка увеличенного текста подтверждает читаемость форм. | evidence/verification-20260717.md | PASS |
| AC-23 | accessibility | Проверка светлого и тёмного оформления подтверждает читаемость. | evidence/verification-20260717.md | PASS |
| AC-24 | accessibility | Проверка повышенного контраста подтверждает читаемость и различимость. | evidence/verification-20260717.md | PASS |
| AC-25 | integration | Сквозной проход подтверждает паритет с iOS-клиентом. | evidence/verification-20260717.md | PASS |
| AND-REQ-1 | architecture | Граф Gradle и инспекция границы проверяют физическое владение оболочки. | evidence/verification-20260717.md | PASS |
| AND-REQ-2 | presentation | Оформление и ресурсные сценарии проверяют доступное представление навигации. | evidence/verification-20260717.md | PASS |
| AND-REQ-3 | architecture | Инспекция корневой маршрутизации и сценарий гейтинга проверяют композицию запуска. | evidence/verification-20260717.md | PASS |
| AND-REQ-4 | tests | Сценарии экранов проверяют флоу: почта, проверка, пароль с заголовком. | evidence/verification-20260717.md | PASS |
| AND-REQ-5 | tests | Сценарии перехода проверяют оболочку после входа и регистрации. | evidence/verification-20260717.md | PASS |
| AND-REQ-6 | tests | Проверка хранилища и перезапуск проверяют сохранение сессии. | evidence/verification-20260717.md | PASS |
| AND-REQ-7 | tests | Сценарии экранов проверяют обработку ошибок и состояний. | evidence/verification-20260717.md | PASS |
| AND-REQ-8 | tests | Сценарии истечения проверяют возврат и очистку данных. | evidence/verification-20260717.md | PASS |
| AND-REQ-9 | security | Проверка хранилища и конфигурации сети проверяют безопасное хранение. | evidence/verification-20260717.md | PASS |
| AND-REQ-10 | accessibility | Проверка доступных технологий, масштабирование и смена оформления проверяют доступность. | evidence/verification-20260717.md | PASS |
| AND-AC-1 | integration | Граф Gradle и инспекция границы проверяют включение оболочки и композицию. | evidence/verification-20260717.md | PASS |
| AND-AC-2 | tests | Сценарии состояния и экранов проверяют переходы и доступную семантику. | evidence/verification-20260717.md | PASS |
| AND-AC-3 | accessibility | Проверка оформления, масштаба, подписей и запасного варианта проверяет оболочку. | evidence/verification-20260717.md | PASS |
| AND-AC-4 | architecture | Граф Gradle и инспекция границы проверяют модульную границу авторизации. | evidence/verification-20260717.md | PASS |
| AND-AC-5 | UI | Сценарий гейтинга проверяет экран входа без сессии и оболочку с сессией. | evidence/verification-20260717.md | PASS |
| AND-AC-6 | UI | Сценарий ветвления проверяет заголовок «Вход» для существующей почты. | evidence/verification-20260717.md | PASS |
| AND-AC-7 | UI | Сценарий ветвления проверяет заголовок «Регистрация» для новой почты. | evidence/verification-20260717.md | PASS |
| AND-AC-8 | UI | Сценарий возврата проверяет сохранение введённой почты. | evidence/verification-20260717.md | PASS |
| AND-AC-9 | UI | Сценарий входа проверяет оболочку с разделом «Кейсы». | evidence/verification-20260717.md | PASS |
| AND-AC-10 | UI | Сценарий регистрации проверяет оболочку с разделом «Кейсы». | evidence/verification-20260717.md | PASS |
| AND-AC-11 | UI | Сценарий перезапуска проверяет оболочку без экрана входа. | evidence/verification-20260717.md | PASS |
| AND-AC-12 | UI | Сценарий ошибки проверяет сообщение без раскрытия и очистку пароля. | evidence/verification-20260717.md | PASS |
| AND-AC-13 | UI | Сценарий пустого поля проверяет объяснение без отправки. | evidence/verification-20260717.md | PASS |
| AND-AC-14 | tests | Тест валидации проверяет отклонение почты до запроса. | evidence/verification-20260717.md | PASS |
| AND-AC-15 | tests | Тест валидации проверяет отклонение короткого пароля до запроса. | evidence/verification-20260717.md | PASS |
| AND-AC-16 | UI | Сценарий ограничения проверяет заблокированную кнопку и время повтора. | evidence/verification-20260717.md | PASS |
| AND-AC-17 | UI | Сценарий конфликта проверяет объяснение о существовании аккаунта. | evidence/verification-20260717.md | PASS |
| AND-AC-18 | tests | Сценарий сети проверяет восстановимое состояние и сохранение почты. | evidence/verification-20260717.md | PASS |
| AND-AC-19 | UI | Сценарий истечения проверяет возврат с объяснением без данных. | evidence/verification-20260717.md | PASS |
| AND-AC-20 | tests | Проверка хранилища подтверждает очистку секрета. | evidence/verification-20260717.md | PASS |
| AND-AC-21 | security | Проверка хранилища подтверждает отсутствие пароля. | evidence/verification-20260717.md | PASS |
| AND-AC-22 | security | Инспекция хранилища подтверждает изоляцию сессии. | evidence/verification-20260717.md | PASS |
| AND-AC-23 | security | Проверка конфигурации сети подтверждает запрет незащищённого трафика. | evidence/verification-20260717.md | PASS |
| AND-AC-24 | accessibility | Доступные технологии подтверждают имена, ошибки и загрузку. | evidence/verification-20260717.md | PASS |
| AND-AC-25 | accessibility | Проверка фокуса подтверждает переход к началу шага. | evidence/verification-20260717.md | PASS |
| AND-AC-26 | accessibility | Визуальная проверка подтверждает нецветовые признаки. | evidence/verification-20260717.md | PASS |
| AND-AC-27 | accessibility | Проверка масштаба текста подтверждает читаемость. | evidence/verification-20260717.md | PASS |
| AND-AC-28 | accessibility | Проверка оформления подтверждает читаемость. | evidence/verification-20260717.md | PASS |
| AND-AC-29 | accessibility | Проверка контраста подтверждает различимость. | evidence/verification-20260717.md | PASS |
| AND-AC-30 | integration | Сравнение с iOS подтверждает паритет шагов и текстов. | evidence/verification-20260717.md | PASS |
| NATIVE-APPEARANCE | presentation | Проверка оформления Material 3 подтверждает согласованность подписей, сообщений и состояний полей. | evidence/native-appearance.json | PASS |
| NATIVE-LIGHT | presentation | Проверка светлого оформления подтверждает читаемость и контраст. | evidence/native-light.json | PASS |
| NATIVE-DARK | presentation | Проверка тёмного оформления подтверждает читаемость и контраст. | evidence/native-dark.json | PASS |
| NATIVE-INCREASED-CONTRAST | presentation | Проверка повышенного контраста подтверждает различимость. | evidence/native-increased-contrast.json | PASS |
| NATIVE-ASSISTIVE-SEMANTICS | accessibility | Проверка доступных технологий подтверждает имена, объявления и состояние. | evidence/native-assistive-semantics.json | PASS |
| NATIVE-TEXT-SCALING | accessibility | Проверка увеличенного текста подтверждает читаемость и работоспособность. | evidence/native-text-scaling.json | PASS |
| NATIVE-MOTION | presentation | Проверка взаимодействий подтверждает сдержанную анимацию без единого носителя состояния. | evidence/native-motion.json | PASS |
| NATIVE-DEVICE-ADAPTATION | presentation | Проверка компоновки подтверждает читаемость на компактном и широком экране. | evidence/native-device-adaptation.json | PASS |
| NATIVE-AVAILABILITY-FALLBACK | presentation | Проверка запасного варианта подтверждает мягко-синий запасной вариант без недоказанных расширений. | evidence/native-availability-fallback.json | PASS |

## Modularity verification

- Dependency graph: PASS
- Public API and visibility: PASS
- Module-level tests: PASS
- Consumer integration and build: PASS
- App-shell allowlist: PASS

## Native UX verification

Готовые решения из `platform-ux.md` проверяются через семантику компонентов Material 3, подписи из ресурсов, признаки состояний, масштабирование шрифта, светлое и тёмное оформление, доступные контрасты и мягко-синий запасной вариант. Доказательства записываются только при реальной среде выполнения; недоступная среда не засчитывается как успешный результат. Русское уточнение: проверяющий фиксирует только наблюдаемое поведение и сохраняет честный статус доказательств.

## Derived method matrix

Выбранный модульный объём требует проверки границы, сборки, публичного контракта, интеграции потребителя, графа зависимостей и соединения с оболочкой. Область экранов добавляет состояние, семантику, доступность, дизайн-систему и проверку времени выполнения. Область приложения добавляет проверку корневой маршрутизации и гейтинга запуска. Русское уточнение: матрица описывает, какие риски покрываются сборкой, состоянием, ресурсами, доступностью и модульной границей.

## Unverified risks

Свежий запуск проверки выполнен на Pixel_6 AVD / API 36. Проверки времени выполнения, доступности, жизненного цикла сессии, сетевой безопасности и живого backend-контракта записаны в `evidence/verification-20260717.md`; открытых непроверенных рисков по Android verify matrix не осталось.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | evidence/native-appearance.json | PASS |
| NATIVE-LIGHT | evidence/native-light.json | PASS |
| NATIVE-DARK | evidence/native-dark.json | PASS |
| NATIVE-INCREASED-CONTRAST | evidence/native-increased-contrast.json | PASS |
| NATIVE-ASSISTIVE-SEMANTICS | evidence/native-assistive-semantics.json | PASS |
| NATIVE-TEXT-SCALING | evidence/native-text-scaling.json | PASS |
| NATIVE-MOTION | evidence/native-motion.json | PASS |
| NATIVE-DEVICE-ADAPTATION | evidence/native-device-adaptation.json | PASS |
| NATIVE-AVAILABILITY-FALLBACK | evidence/native-availability-fallback.json | PASS |

## Open questions

None.
