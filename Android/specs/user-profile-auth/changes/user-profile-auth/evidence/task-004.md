# Итог

Реализован корневой шлюз авторизации с проверкой сессии при запуске, интеграция приложения с модулем авторизации и конфигурация сетевой безопасности. Шлюз читает сессионный секрет из защищённого хранилища: при валидной сессии немедленно вызывает обратный вызов для показа оболочки, при невалидной — показывает экран авторизации. Приложение зависит от модуля авторизации и компонуется только шлюз авторизации; логика авторизации остаётся в модуле-библиотеке. Конфигурация сетевой безопасности запрещает открытый трафик и доверяет только системным сертификатам. Модульная граница подтверждена: модуль авторизации не зависит от приложения и оболочки. Сборка потребителя успешна, юнит-тесты пройдены.

# Технические доказательства

```
Changed paths:
Android/auth/src/main/java/ru/home/sysdevsc/auth/AuthGate.kt — existing, modified
Android/auth/src/main/java/ru/home/sysdevsc/auth/data/DefaultAuthApiService.kt — proposed, created
Android/auth/src/main/java/ru/home/sysdevsc/auth/data/EncryptedSessionRepository.kt — proposed, created
Android/app/build.gradle.kts — existing, modified
Android/app/src/main/java/ru/home/sysdevsc/MainActivity.kt — existing, modified
Android/app/src/main/AndroidManifest.xml — existing, modified
Android/app/src/main/res/xml/network_security_config.xml — proposed, created
```

Шлюз авторизации:
- При запуске читает сессионный секрет через EncryptedSessionRepository
- Валидная сессия вызывает onAuthenticated — потребитель показывает оболочку
- Невалидная сессия показывает AuthScreen с шагом почты
- Успешная авторизация сохраняет сессию и вызывает onAuthenticated
- Фабрика AuthViewModelFactory внедряет зависимости в ViewModel
- Зависимости создаются по умолчанию из контекста приложения
- Не зависит от модуля app-shell, не компонуется оболочку напрямую

DefaultAuthApiService.kt:
- Реализация сетевого контракта на базе OkHttp
- Запросы по HTTPS: проверка почты, вход, регистрация
- Ответы 200 — успех с токеном, 401 — неверные данные, 409 — занятая почта, 422 — почта не найдена, 429 — ограничение, прочее — ошибка
- Сетевые ошибки — офлайн

EncryptedSessionRepository.kt:
- Реализация SessionRepository на базе EncryptedSharedPreferences
- Хранит сессионный токен в зашифрованном хранилище
- Использует мастер-ключ AES256_GCM

MainActivity.kt:
- SysDevScApp компонует шлюз авторизации вместо прямой оболочки
- Флаг isAuthenticated управляет переключением между шлюзом и оболочкой
- Тема приложения и полноэкранный режим сохранены

app/build.gradle.kts:
- Добавлена зависимость от модуля авторизации

AndroidManifest.xml:
- Подключена конфигурация сетевой безопасности

network_security_config.xml:
- Отключён открытый трафик, доверие только системным сертификатам

# Проверки

- Сборка потребителя успешна — app:assembleDebug
- Юнит-тесты пройдены — app:testDebugUnitTest
- Модульная граница подтверждена — `module boundary`
- Сборка модуля проходит — `module build`
- Публичный контракт доступен — `public contract`
- Потребитель интегрирован — `consumer integration`
- Граф зависимостей верен — `dependency graph`
- Подключение оболочки завершено — `app-shell wiring`
- Направление зависимостей: приложение зависит от авторизации, авторизация не зависит от приложения
- Конфигурация сетевой безопасности запрещает открытый трафик
