# Evidence AC-1 — simulator launch и три направления

Статус: PASS.

Fresh test command на `iPhone 17 Pro` с iOS 26.5 завершилась `TEST SUCCEEDED`.
UI tests нашли ровно утверждённые направления «Кейсы», «Знания», «Профиль» в
таббаре и подтвердили, что navigation остаётся доступной после запуска и
после переходов.

Дополнительный simulator launch через `simctl launch` успешно запустил bundle
`none.SysDevScen`, а screenshot `/tmp/verify-app-shell-light.png` показал
первую поверхность «Кейсы» и три navigation items.
