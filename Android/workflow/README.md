# Android workflow

Android поддерживает `propose`, `plan`, `implement`, `verify` и implementation
archive. Adapter выбирает только evidence-backed scopes; Compose, multiplatform,
DI framework, lint tools, modules, variants и Gradle tasks не предполагаются.

Product-backed `ui` использует
[`roles/android-ux-designer.md`](roles/android-ux-designer.md) для Material 3
`platform-ux.md`; M3 Expressive и dynamic color evidence-conditional.

Phase addenda:

- [`phases/propose.md`](phases/propose.md) — discovered module decision и
  structured boundary guard;
- [`phases/plan.md`](phases/plan.md) — module/API/consumer/app-shell task wiring;
- [`phases/implement.md`](phases/implement.md) — sealed module/deviation writes;
- [`phases/verify.md`](phases/verify.md) — production read-only terminal evidence;
- [`phases/archive.md`](phases/archive.md) — Android namespace/fingerprint поверх
  общего collision-safe archive.

Read-only deep review расширяется
[`phases/deep-code-review.md`](phases/deep-code-review.md). Addendum выбирает
только обнаруженные Android lenses и после fix возвращает `verify android`, не
заявляя fixed/verified внутри review.

Architecture baseline пересказывает [Android architecture guide](https://developer.android.com/topic/architecture) и [recommendations](https://developer.android.com/topic/architecture/recommendations).
Modularity addendum следует official
[guide](https://developer.android.com/topic/modularization) и
[patterns](https://developer.android.com/topic/modularization/patterns).
Common modularity и `rules/architecture/modularization.md` входят во все четыре
base profiles; adapter `modularity` связывает их с isolation scope `module` и
обнаруженными Gradle Android/Kotlin physical units.
