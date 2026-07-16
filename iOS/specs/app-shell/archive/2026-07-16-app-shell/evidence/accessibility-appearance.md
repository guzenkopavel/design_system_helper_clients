# Evidence REQ-5 — accessibility и appearance

Статус: PASS.

UI tests подтвердили visible labels «Кейсы», «Знания», «Профиль», selected state
через `XCUIElement.isSelected` и перенос выбранности между разделами. Runtime
screenshots `/tmp/verify-app-shell-light.png`, `/tmp/verify-app-shell-dark.png`
и `/tmp/verify-app-shell-contrast-dynamic-type.png` подтвердили читаемые labels,
нейтральную поверхность и нецветовой selected cue через системную pill/иконку.

Static source check не нашёл custom `Color`, `.font`, `.padding`, `.background`,
material, blur, glass или explicit animation. Поэтому `Reduce Transparency` и
`Reduce Motion` остаются системным fallback стандартных controls.
