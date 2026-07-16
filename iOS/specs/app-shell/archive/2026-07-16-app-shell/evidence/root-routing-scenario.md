# Evidence REQ-3 — маршрутизация трёх разделов

Статус: PASS.

UI test `testSelectionMovesBetweenAllSectionsWithoutTemplateControls` прошёл
путь «Знания» → «Профиль» → «Кейсы». После каждого выбора runtime проверил
соответствующий visible title и selected tab. UI test
`testRepeatedSelectionDoesNotHideShellNavigation` подтвердил, что повторный
выбор «Кейсы» не скрывает shell navigation и не создаёт вторичное состояние.

Source contract использует один `TabView(selection:)` и закрытый набор
`RootSection`, поэтому route не принимает внешние или неутверждённые значения.
