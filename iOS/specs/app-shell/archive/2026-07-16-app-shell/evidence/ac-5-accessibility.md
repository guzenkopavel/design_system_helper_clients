# Evidence AC-5 — assistive и appearance результат

Статус: PASS.

Visible/accessibility labels берутся из одного `section.title`, а `Label` внутри
standard `TabView` отдаёт нативную роль и selected semantics. UI tests
подтвердили selected state через accessibility automation, а screenshots
подтвердили readable labels в light, dark, increased contrast и Dynamic Type.

В source нет custom color-only state, custom material, blur, glass simulation
или explicit animation; выбранность поддерживается системной формой, иконкой и
label emphasis.
