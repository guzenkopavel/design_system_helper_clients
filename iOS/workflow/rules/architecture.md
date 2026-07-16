# iOS architecture

Индекс архитектурного baseline. Это набор lenses, а не требование создать все
слои. Propose сначала исследует реальный composition root, module/package
boundaries и ownership. Greenfield решения помечаются provisional.

| Тема | Файл |
|---|---|
| Feature-First | [`architecture/feature-first.md`](architecture/feature-first.md) |
| Physical packages/targets | [`package-development.md`](package-development.md) |
| DI | [`architecture/dependency-injection.md`](architecture/dependency-injection.md) |
| Use Cases | [`architecture/use-cases.md`](architecture/use-cases.md) |
| Errors | [`architecture/error-handling.md`](architecture/error-handling.md) |
| MVVM | [`architecture/mvvm.md`](architecture/mvvm.md) |
| Naming | [`architecture/naming.md`](architecture/naming.md) |
| Existing/legacy fit | [`architecture/legacy.md`](architecture/legacy.md) |
| Type design | [`architecture/types-clean-code.md`](architecture/types-clean-code.md) |

## Общие инварианты

- Dependency direction защищает domain behavior от UI, persistence и transport.
- Feature владеет своим поведением и state; shared-код не становится складом
  случайных helpers.
- Public surface минимален и выражен типами. Cross-feature связь проходит через
  контракт, а не через внутренний concrete type.
- Composition и lifecycle dependencies явны. Global mutable state запрещён.
- Data/control/error/cancellation flows описываются вместе; happy path
  недостаточен.
- Architecture decision получает task paths, verification method и migration
  strategy. Диаграмма без исполнимого контракта не считается решением.
- App target — composition shell, а не default owner feature/data/network code.
  Любое отклонение следует structured `isolated | deviation | not-applicable`
  contract из common modularity rule и проверяется boundary guard. `deviation`
  никогда не разрешает capability ownership в app target.

Сначала проверять реальную структуру клиента: правила задают направление, но не
разрешают выдумывать существующие modules, targets, packages или paths.
