# Evidence — task-002

## Резюме

Создан сетевой клиент DefaultAuthAPIClient поверх URLSession с временной конфигурацией, отключённым кэшем и cookie. Нормализован конверт ошибок в доменные типы. Реализованы DTO для четырёх операций: проверка почты, вход, регистрация, профиль. Тесты с фикстурами подтверждают декодирование ответов и извлечение сессионного токена.

## Изменённые файлы

```
iOS/AuthFeature/Sources/AuthFeature/Data/DTO/EmailCheckResponse.swift
iOS/AuthFeature/Sources/AuthFeature/Data/DTO/LoginResponse.swift
iOS/AuthFeature/Sources/AuthFeature/Data/DTO/RegisterResponse.swift
iOS/AuthFeature/Sources/AuthFeature/Data/DTO/ProfileResponse.swift
iOS/AuthFeature/Sources/AuthFeature/Data/DTO/ErrorEnvelopeResponse.swift
iOS/AuthFeature/Sources/AuthFeature/Data/DefaultAuthAPIClient.swift
iOS/AuthFeature/Tests/AuthFeatureTests/Data/DefaultAuthAPIClientTests.swift
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/EmailCheckSuccess.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/LoginSuccess.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/RegisterSuccess.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ProfileSuccess.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorInvalidCredentials.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorEmailConflict.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorValidation.json
iOS/AuthFeature/Tests/AuthFeatureTests/Fixtures/ErrorRateLimited.json
```

## Фокусированные проверки

Команда тестирования пакета: 14 тестов, 0 провалов.
- Все DTO декодируются корректно
- Извлечение сессионного токена из Set-Cookie работает
- Ошибки конверта декодируются с полями кода, сообщения, повторяемости и трассировки

## Статический обзор области

- Защищённый канал: клиент проверяет https перед отправкой
- Кэш отключён: временная конфигурация, политика cookie отключена
- Автоповтор отсутствует
- Отмена пробрасывается без преобразования
- Изоляция: клиент передаваем (actor), не удерживает мутабельное состояние
- Потребитель пакета: пакет собирается с клиентом
- Публичный контракт: клиент закрыт за протоколом AuthAPIClient
- Граф зависимостей: направление от данных к домену
- Подключение оболочки: клиент не знает о потребителе
