# Evidence AC-2 — начальная selected semantics

Статус: PASS.

UI test `testLaunchShowsCasesFirstAndKeepsNavigationAvailable` подтвердил, что
после запуска tab «Кейсы» существует и имеет `isSelected == true`, а tabs
«Знания» и «Профиль» существуют и не выбраны. Source contract задаёт начальное
значение `selectedSection` как `.cases`.

Визуальная проверка screenshot показала системный selected cue не только цветом:
активный item имеет pill treatment, icon emphasis и label emphasis.
