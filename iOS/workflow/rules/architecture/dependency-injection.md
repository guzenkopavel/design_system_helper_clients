# Dependency injection

Dependencies создаются в composition root и передаются через initializer.
Stateful global singletons запрещены; stateless shared instance допустим только
при thread-safety и test isolation. Тяжёлые/редкие dependencies создаются factory.

Contracts принадлежат Domain, implementations — Data. Package публикует только
необходимый assembly/factory/API. Design фиксирует lifecycle, reset semantics и
composition point; не привязывается к конкретному DI framework без evidence.
