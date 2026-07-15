# iOS application development

Правило применяется к application/extension targets после discovery реальной
структуры. Не предполагаются конкретные lifecycle framework, minimum OS,
navigation library или dependency container.

## Application boundaries

- Найти app/scene entry points, composition roots, navigation ownership,
  configuration sources и extension boundaries.
- Startup выполняет только обязательную работу; тяжёлый I/O откладывается или
  измеренно распараллеливается без нарушения dependency order.
- App/scene state transitions идемпотентны и не создают повторные observers,
  tasks или registrations.
- Deep links, notifications и external URLs проходят typed parsing, validation
  и авторизационные checks до navigation.
- Background work имеет expiration/cancellation handling и не обещает
  не гарантированное системой время выполнения.
- Sensitive configuration не хранится в source/logs; entitlement/permission
  изменения минимальны и проверяемы.

## UI/state integration

UI state обновляется на корректном actor, navigation вызывается через найденный
owner, restoration/fallback описаны для пользовательски значимых flows.
Application service не превращается в global mutable singleton. Extensions и
widgets используют только доступные им contracts/storage и отдельную build/run
проверку.

Verify включает targeted build и runtime scenario на доступном simulator/device.
Cold/warm launch, background/foreground и failure path проверяются, когда они
затронуты. Универсального launch threshold нет: budget появляется только из
измеренного baseline/продуктового SLO.
