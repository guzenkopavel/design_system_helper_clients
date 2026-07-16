# Android direction

Корень: [`../../Android/`](../../Android/).

Здесь размещать только Android-специфичные расширения: Gradle/build variants,
Kotlin/Compose/View conventions, Emulator и Android UI automation. Общий
контракт дизайн-системы и процесса оставлять в `workflow/`.

Продуктовая спека находится в [`specs/product/`](../../specs/product/), а
Android-специфика реализации — в [`Android/specs/`](../../Android/specs/).
Реализация в режиме `product-backed` ссылается на общий
`READY`/`APPROVED`-контракт и не переопределяет его. `technical-only`
допускается без shared spec только при доказанном
`Product impact assessment: NONE`.

Android adapter и addenda поддерживают `propose/plan/implement/verify` и
implementation archive. Verify сохраняет sealed rule selection, обнаруживает
commands/infrastructure из repository и Plan и пишет только scoped evidence.
Archive использует fresh fingerprint и общий collision-safe algorithm. Product
archive остаётся отдельным shared lifecycle. Compose/KMP и tooling scopes
выбираются только по repository evidence; iOS rules не наследуются.

`$deep-code-review review|feedback|bug android <feature> [--change ...]`
использует только Android addendum и обнаруженные repository conventions. Skill
read-only; после отдельного fix возвращается route `verify android`, но
fixed/verified до отдельного успешного lifecycle не заявляется.

`pre_commit` profile этого adapter владеет Android source, Gradle/project,
credential/keystore, security, UI и resource globs. Общий gate не содержит
Android-specific значений; Android evidence трактуется по
[`pre-commit-check.md`](../../Android/workflow/phases/pre-commit-check.md).

Product-backed `ui` добавляет sequential `android-ux-designer` и
`platform-ux.md`: Material 3 baseline, а M3 Expressive/dynamic color остаются
evidence-conditional.
