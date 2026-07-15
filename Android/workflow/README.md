# Android workflow

Android поддерживает `propose`, `plan`, `implement`. `verify` и implementation archive отсутствуют в capabilities и блокируются до записи. Adapter выбирает только evidence-backed scopes; Compose, multiplatform, DI framework, lint tools и Gradle tasks не предполагаются.

Read-only deep review расширяется
[`phases/deep-code-review.md`](phases/deep-code-review.md). Addendum выбирает
только обнаруженные Android lenses и не заявляет terminal Verify после fix.

Architecture baseline пересказывает [Android architecture guide](https://developer.android.com/topic/architecture) и [recommendations](https://developer.android.com/topic/architecture/recommendations).
