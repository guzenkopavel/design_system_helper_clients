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

Android adapter и addenda поддерживают `propose/plan/implement`. Verify и
implementation archive отсутствуют в `lifecycle_capabilities` и блокируются до
записи. Product archive остаётся отдельным shared lifecycle. Compose/KMP и
tooling scopes выбираются только по repository evidence; iOS rules не
наследуются.

`pre_commit` profile этого adapter владеет Android source, Gradle/project,
credential/keystore, security, UI и resource globs. Общий gate не содержит
Android-specific значений; Android evidence трактуется по
[`pre-commit-check.md`](../../Android/workflow/phases/pre-commit-check.md).
