# Android addendum: Implement

После scoped code dispatch read-only `android-kotlin-reviewer`. При реальном build failure вызвать `android-build-diagnostician`; repeated identical failure останавливает цикл. Единственный writer — common `implementation-writer`. Verify не запускать.

Product-backed UI перечитывает immutable `platform-ux.md` и фиксирует Material
3, light/dark, accessible on-colors, dynamic-color и soft-blue fallback evidence.
