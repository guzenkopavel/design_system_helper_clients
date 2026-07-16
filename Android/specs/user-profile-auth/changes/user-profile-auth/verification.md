# Verification — user-profile-auth / Android / user-profile-auth

| Contract ID | Layer | Method | Evidence path | Status |
|---|---|---|---|---|
| REQ-1 | integration | Проверка корневой маршрутизации подтверждает, что без сессии оболочка недоступна. | evidence/verification.md | pending |
| REQ-2 | integration | Сценарии проверки флоу подтверждают ветвление по почте и возврат к первому шагу. | evidence/verification.md | pending |
| REQ-3 | integration | Сценарии успешного входа и регистрации подтверждают переход в оболочку с разделом «Кейсы». | evidence/verification.md | pending |
| REQ-4 | integration | Проверка перезапуска подтверждает сохранение и восстановление сессии. | evidence/verification.md | pending |
| REQ-5 | integration | Сценарии ошибок подтверждают различимость и восстановимость всех наблюдаемых состояний. | evidence/verification.md | pending |
| REQ-6 | integration | Сценарии истечения сессии подтверждают возврат на экран входа и очистку данных. | evidence/verification.md | pending |
| REQ-7 | security | Проверка хранилища и конфигурации сети подтверждает защищённое хранение и передачу. | evidence/verification.md | pending |
| REQ-8 | accessibility | Проверка доступных технологий, масштабирование и смена оформления подтверждают доступность. | evidence/verification.md | pending |
| REQ-9 | integration | Сценарий сравнения с iOS подтверждает идентичные шаги, тексты и правила гейтинга. | evidence/verification.md | pending |
| AC-1 | UI | Сценарий запуска без сессии подтверждает экран входа и отсутствие навигации. | evidence/verification.md | pending |
| AC-2 | UI | Сценарий ввода существующей почты подтверждает заголовок «Вход». | evidence/verification.md | pending |
| AC-3 | UI | Сценарий ввода новой почты подтверждает заголовок «Регистрация». | evidence/verification.md | pending |
| AC-4 | UI | Сценарий возврата подтверждает сохранение введённой почты. | evidence/verification.md | pending |
| AC-5 | UI | Сценарий успешного входа подтверждает оболочку с разделом «Кейсы». | evidence/verification.md | pending |
| AC-6 | UI | Сценарий успешной регистрации подтверждает оболочку с разделом «Кейсы». | evidence/verification.md | pending |
| AC-7 | UI | Сценарий перезапуска подтверждает оболочку без экрана входа. | evidence/verification.md | pending |
| AC-8 | UI | Сценарий неверного пароля подтверждает ошибку и очистку поля. | evidence/verification.md | pending |
| AC-9 | UI | Сценарий пустого поля подтверждает объяснение без отправки запроса. | evidence/verification.md | pending |
| AC-10 | tests | Тест локальной валидации почты подтверждает отклонение до запроса. | evidence/verification.md | pending |
| AC-11 | tests | Тест локальной валидации пароля подтверждает отклонение короткого пароля. | evidence/verification.md | pending |
| AC-12 | UI | Сценарий ограничения попыток подтверждает состояние с указанием времени. | evidence/verification.md | pending |
| AC-13 | UI | Сценарий занятой почты подтверждает объяснение о существовании аккаунта. | evidence/verification.md | pending |
| AC-14 | tests | Сценарий отсутствия сети подтверждает восстановимое состояние. | evidence/verification.md | pending |
| AC-15 | UI | Сценарий истечения сессии подтверждает возврат на вход с объяснением. | evidence/verification.md | pending |
| AC-16 | tests | Проверка хранилища подтверждает очистку недействительного секрета. | evidence/verification.md | pending |
| AC-17 | security | Проверка хранилища подтверждает отсутствие пароля. | evidence/verification.md | pending |
| AC-18 | security | Инспекция хранилища подтверждает изоляцию сессионных данных. | evidence/verification.md | pending |
| AC-19 | accessibility | Доступные технологии подтверждают имена полей, действий и объявление ошибок. | evidence/verification.md | pending |
| AC-20 | accessibility | Проверка фокуса подтверждает переход к началу нового шага. | evidence/verification.md | pending |
| AC-21 | accessibility | Визуальная проверка подтверждает различимость без опоры на цвет. | evidence/verification.md | pending |
| AC-22 | accessibility | Проверка увеличенного текста подтверждает читаемость форм. | evidence/verification.md | pending |
| AC-23 | accessibility | Проверка светлого и тёмного оформления подтверждает читаемость. | evidence/verification.md | pending |
| AC-24 | accessibility | Проверка повышенного контраста подтверждает читаемость и различимость. | evidence/verification.md | pending |
| AC-25 | integration | Сквозной проход подтверждает паритет с iOS-клиентом. | evidence/verification.md | pending |
| AND-REQ-1 | architecture | Граф Gradle и инспекция границы проверяют физическое владение оболочки. | evidence/verification.md | pending |
| AND-REQ-2 | presentation | Оформление и ресурсные сценарии проверяют доступное представление навигации. | evidence/verification.md | pending |
| AND-REQ-3 | architecture | Инспекция корневой маршрутизации и сценарий гейтинга проверяют композицию запуска. | evidence/verification.md | pending |
| AND-REQ-4 | tests | Сценарии экранов проверяют флоу: почта, проверка, пароль с заголовком. | evidence/verification.md | pending |
| AND-REQ-5 | tests | Сценарии перехода проверяют оболочку после входа и регистрации. | evidence/verification.md | pending |
| AND-REQ-6 | tests | Проверка хранилища и перезапуск проверяют сохранение сессии. | evidence/verification.md | pending |
| AND-REQ-7 | tests | Сценарии экранов проверяют обработку ошибок и состояний. | evidence/verification.md | pending |
| AND-REQ-8 | tests | Сценарии истечения проверяют возврат и очистку данных. | evidence/verification.md | pending |
| AND-REQ-9 | security | Проверка хранилища и конфигурации сети проверяют безопасное хранение. | evidence/verification.md | pending |
| AND-REQ-10 | accessibility | Проверка доступных технологий, масштабирование и смена оформления проверяют доступность. | evidence/verification.md | pending |
| AND-AC-1 | integration | Граф Gradle и инспекция границы проверяют включение оболочки и композицию. | evidence/verification.md | pending |
| AND-AC-2 | tests | Сценарии состояния и экранов проверяют переходы и доступную семантику. | evidence/verification.md | pending |
| AND-AC-3 | accessibility | Проверка оформления, масштаба, подписей и запасного варианта проверяет оболочку. | evidence/verification.md | pending |
| AND-AC-4 | architecture | Граф Gradle и инспекция границы проверяют модульную границу авторизации. | evidence/verification.md | pending |
| AND-AC-5 | UI | Сценарий гейтинга проверяет экран входа без сессии и оболочку с сессией. | evidence/verification.md | pending |
| AND-AC-6 | UI | Сценарий ветвления проверяет заголовок «Вход» для существующей почты. | evidence/verification.md | pending |
| AND-AC-7 | UI | Сценарий ветвления проверяет заголовок «Регистрация» для новой почты. | evidence/verification.md | pending |
| AND-AC-8 | UI | Сценарий возврата проверяет сохранение введённой почты. | evidence/verification.md | pending |
| AND-AC-9 | UI | Сценарий входа проверяет оболочку с разделом «Кейсы». | evidence/verification.md | pending |
| AND-AC-10 | UI | Сценарий регистрации проверяет оболочку с разделом «Кейсы». | evidence/verification.md | pending |
| AND-AC-11 | UI | Сценарий перезапуска проверяет оболочку без экрана входа. | evidence/verification.md | pending |
| AND-AC-12 | UI | Сценарий ошибки проверяет сообщение без раскрытия и очистку пароля. | evidence/verification.md | pending |
| AND-AC-13 | UI | Сценарий пустого поля проверяет объяснение без отправки. | evidence/verification.md | pending |
| AND-AC-14 | tests | Тест валидации проверяет отклонение почты до запроса. | evidence/verification.md | pending |
| AND-AC-15 | tests | Тест валидации проверяет отклонение короткого пароля до запроса. | evidence/verification.md | pending |
| AND-AC-16 | UI | Сценарий ограничения проверяет заблокированную кнопку и время повтора. | evidence/verification.md | pending |
| AND-AC-17 | UI | Сценарий конфликта проверяет объяснение о существовании аккаунта. | evidence/verification.md | pending |
| AND-AC-18 | tests | Сценарий сети проверяет восстановимое состояние и сохранение почты. | evidence/verification.md | pending |
| AND-AC-19 | UI | Сценарий истечения проверяет возврат с объяснением без данных. | evidence/verification.md | pending |
| AND-AC-20 | tests | Проверка хранилища подтверждает очистку секрета. | evidence/verification.md | pending |
| AND-AC-21 | security | Проверка хранилища подтверждает отсутствие пароля. | evidence/verification.md | pending |
| AND-AC-22 | security | Инспекция хранилища подтверждает изоляцию сессии. | evidence/verification.md | pending |
| AND-AC-23 | security | Проверка конфигурации сети подтверждает запрет незащищённого трафика. | evidence/verification.md | pending |
| AND-AC-24 | accessibility | Доступные технологии подтверждают имена, ошибки и загрузку. | evidence/verification.md | pending |
| AND-AC-25 | accessibility | Проверка фокуса подтверждает переход к началу шага. | evidence/verification.md | pending |
| AND-AC-26 | accessibility | Визуальная проверка подтверждает нецветовые признаки. | evidence/verification.md | pending |
| AND-AC-27 | accessibility | Проверка масштаба текста подтверждает читаемость. | evidence/verification.md | pending |
| AND-AC-28 | accessibility | Проверка оформления подтверждает читаемость. | evidence/verification.md | pending |
| AND-AC-29 | accessibility | Проверка контраста подтверждает различимость. | evidence/verification.md | pending |
| AND-AC-30 | integration | Сравнение с iOS подтверждает паритет шагов и текстов. | evidence/verification.md | pending |
| NATIVE-APPEARANCE | presentation | Проверка оформления Material 3 подтверждает согласованность подписей, сообщений и состояний полей. | evidence/verification.md | pending |
| NATIVE-LIGHT | presentation | Проверка светлого оформления подтверждает читаемость и контраст. | evidence/verification.md | pending |
| NATIVE-DARK | presentation | Проверка тёмного оформления подтверждает читаемость и контраст. | evidence/verification.md | pending |
| NATIVE-INCREASED-CONTRAST | presentation | Проверка повышенного контраста подтверждает различимость. | evidence/verification.md | pending |
| NATIVE-ASSISTIVE-SEMANTICS | accessibility | Проверка доступных технологий подтверждает имена, объявления и состояние. | evidence/verification.md | pending |
| NATIVE-TEXT-SCALING | accessibility | Проверка увеличенного текста подтверждает читаемость и работоспособность. | evidence/verification.md | pending |
| NATIVE-MOTION | presentation | Проверка взаимодействий подтверждает сдержанную анимацию без единого носителя состояния. | evidence/verification.md | pending |
| NATIVE-DEVICE-ADAPTATION | presentation | Проверка компоновки подтверждает читаемость на компактном и широком экране. | evidence/verification.md | pending |
| NATIVE-AVAILABILITY-FALLBACK | presentation | Проверка запасного варианта подтверждает мягко-синий fallback без недоказанных расширений. | evidence/verification.md | pending |

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

## Native UX verification

Готовые решения из `platform-ux.md` проверяются через семантику компонентов Material 3, подписи из ресурсов, признаки состояний, масштабирование шрифта, светлое и тёмное оформление, доступные контрасты и мягко-синий запасной вариант. Доказательства записываются только при реальной среде выполнения; недоступная среда не засчитывается как успешный результат. Русское уточнение: проверяющий фиксирует только наблюдаемое поведение и сохраняет честный статус доказательств.

## Derived method matrix

Выбранный модульный объём требует проверки границы, сборки, публичного контракта, интеграции потребителя, графа зависимостей и соединения с оболочкой. Область экранов добавляет состояние, семантику, доступность, дизайн-систему и проверку времени выполнения. Область приложения добавляет проверку корневой маршрутизации и гейтинга запуска. Русское уточнение: матрица описывает, какие риски покрываются сборкой, состоянием, ресурсами, доступностью и модульной границей.

## Unverified risks

На этапе предложения не найдены устройство или эмулятор. Доступные технологии, повышенный контраст, воссоздание жизненного цикла и проверка сетевой безопасности требуют свежего запуска проверки с подходящей средой выполнения и не могут выводиться из статического дизайна пакета. Русское уточнение: эти риски остаются открытыми до свежего запуска проверки.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | pending | pending |
| NATIVE-LIGHT | pending | pending |
| NATIVE-DARK | pending | pending |
| NATIVE-INCREASED-CONTRAST | pending | pending |
| NATIVE-ASSISTIVE-SEMANTICS | pending | pending |
| NATIVE-TEXT-SCALING | pending | pending |
| NATIVE-MOTION | pending | pending |
| NATIVE-DEVICE-ADAPTATION | pending | pending |
| NATIVE-AVAILABILITY-FALLBACK | pending | pending |

## Open questions

None.