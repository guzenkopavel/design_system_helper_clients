# Android addendum: Implement

После scoped code dispatch read-only `android-kotlin-reviewer`. При реальном build failure вызвать `android-build-diagnostician`; repeated identical failure останавливает цикл. Единственный writer — common `implementation-writer`. Verify не запускать.

Product-backed UI перечитывает immutable `platform-ux.md` и фиксирует Material
3, light/dark, accessible on-colors, dynamic-color и soft-blue fallback evidence.

Для v1 следовать sealed modularity outcome: feature/data/network/storage logic и
mutable state не попадают в application module; writer меняет только physical
module/deviation и composition wiring из task paths.
Registry-anchored v0 завершает только historical task paths/checks и normal
status/evidence transitions. V1 composition rule к нему ретроактивно не
применяется, но ownership и immutable package structure расширять запрещено.
