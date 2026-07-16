# Evidence AC-3 — переходы и перенос selected state

Статус: PASS.

UI test `testSelectionMovesBetweenAllSectionsWithoutTemplateControls` нажал
«Знания», «Профиль» и «Кейсы». После каждого действия проверены visible title
активной поверхности и `isSelected` у соответствующего tab.

Поведение реализовано через один `@State selectedSection` и `TabView(selection:)`,
поэтому одновременно активен только один раздел, а переходы остаются внутри
одной app-shell поверхности.
