# Dependency injection

Dependencies создаются в composition root и передаются через initializer.
Stateful global singletons запрещены; stateless shared instance допустим только
при thread-safety и test isolation. Тяжёлые/редкие dependencies создаются factory.

Contracts принадлежат Domain, implementations — Data. Package публикует только
необходимый assembly/factory/API. Design фиксирует lifecycle, reset semantics и
composition point; не привязывается к конкретному DI framework без evidence.

## Lifetimes

- `transient` подходит stateless/lightweight dependency;
- scoped lifetime требует явного owner (feature flow, scene, session);
- process lifetime допустим только для действительно process-wide service и
  обязан иметь test reset/isolated construction path.

Factory не скрывает service locator. Closure injection уместен для одного
узкого действия; растущий набор closures заменяется cohesive protocol.
Environment-based injection ограничивается UI tree и не переносит business
dependency в implicit global context.

Tests создают system under test с локальными fakes. Если объект невозможно
создать без application singleton, boundary считается недостаточно отделённой.
