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
