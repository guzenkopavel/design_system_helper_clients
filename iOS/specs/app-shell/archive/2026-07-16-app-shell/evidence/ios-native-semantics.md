# Evidence IOS-REQ-2 — native semantics

Статус: PASS.

Нативная поверхность использует standard SwiftUI `TabView(selection:)`,
`Label(section.title, systemImage:)` и `ContentUnavailableView`. UI tests
проверили launch, labels, selected state и перенос выбора. Source contract
содержит accessibility identifiers для активных surfaces:
`root-section-cases`, `root-section-knowledge`, `root-section-profile`.

`Liquid Glass` не интегрирован как custom effect; отсутствие material/blur/glass
в source подтверждает standard opaque semantic fallback.
