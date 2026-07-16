# Evidence IOS-AC-2 — semantic UI path

Статус: PASS.

Focused UI tests прошли нативный semantic path через tab bar buttons «Кейсы»,
«Знания», «Профиль». Для каждого перехода проверены visible surface title и
selected state соответствующего tab. Initial state «Кейсы» проверен отдельно.

Runtime appearance screenshots подтвердили, что selected item сохраняет
нецветовой cue и labels остаются читаемыми при light/dark, increased contrast
и Dynamic Type.
