# Plan — user-profile-auth / iOS / user-profile-auth

## Planning frame

План декомпозирует контракт на девять вертикальных задач c TDD-порядком.
Области: `application`, `concurrency`, `networking`, `package`, `ui`.
Зависимости образуют ациклический граф от фундамента к потребителю.

## DAG

```
task-001 → task-002 → task-004 → task-005 → task-006 → task-007 → task-008 → task-009
task-001 → task-003 → task-004
```

- task-001: доменный фундамент и манифест пакета
- task-002: сетевой клиент и конверт ошибок
- task-003: хранилище секрета
- task-004: реализация вариантов использования
- task-005: автомат состояний и модель представления
- task-006: представление на интерфейсе
- task-007: фабрика композиции и открытый контракт
- task-008: интеграция c приложением и корневая композиция
- task-009: сквозные тесты интерфейса и проход паритета

## Estimates and multipliers

Оценки задач в идеальных днях:

- task-001: 0.5–1 (домен, пакет)
- task-002: 1–1.5 (сеть, конкурентность, пакет)
- task-003: 0.5–1 (хранение, пакет)
- task-004: 1–1.5 (домен, конкурентность)
- task-005: 1–1.5 (конкурентность, интерфейс)
- task-006: 1–1.5 (интерфейс)
- task-007: 0.5–1 (инфраструктура, пакет)
- task-008: 1–1.5 (инфраструктура, пакет)
- task-009: 1–1.5 (интерфейс, тесты)

Команды сборки и тестов:

- Сборка пакета: `xcodebuild -scheme AuthFeature -destination 'generic/platform=iOS Simulator' build`
- Тесты пакета: `xcodebuild -scheme AuthFeature -destination 'platform=iOS Simulator,name=iPhone 16' test`
- Сборка потребителя: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 16' build`
- Тесты потребителя: `xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 16' test`

Watchdog: максимум 300 секунд, stall 120 секунд, вывод 256 KB.

## Verification strategy

Модульные тесты пакета покрывают домен, сеть, хранилище, варианты
использования, автомат состояний и конкурентность. Интеграционные проверки
потребителя подтверждают маршрутизацию по состоянию сессии. Тесты интерфейса
проверяют проверку сессии при запуске, ветвление, возврат, состояния ошибок
и паритет на заглушке. Каждое требование получает отдельное подтверждение
в фазе проверки.
