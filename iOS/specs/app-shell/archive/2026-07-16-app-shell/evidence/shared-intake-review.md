# Evidence REQ-1 — общий договор и iOS-композиция

Статус: PASS.

Проверены `specs/product/app-shell/spec.md`, `iOS/specs/app-shell/changes/app-shell/implementation-spec.md`,
`iOS/specs/app-shell/changes/app-shell/design.md`, `SysDevScenApp.swift` и
`ContentView.swift`. Общий договор требует три постоянных направления в порядке
«Кейсы», «Знания», «Профиль»; iOS-композиция запускает `ContentView`, а
`ContentView` собирает `TabView(selection:)` через закрытый `RootSection` с тем
же порядком.

Production scope не добавляет данные, сеть, хранение, account state, analytics
или отдельную feature boundary. Наблюдаемое поведение остаётся iOS-адаптацией
общего app-shell договора.
