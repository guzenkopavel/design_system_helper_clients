# iOS addendum: Deep Code Review

Сначала использовать active package `engineering_scopes` и точный
`applicable_rule_files`. Без package/path-only review явно перечислить выбранные
risk lenses и причину каждого.

По evidence применять Swift/style, architecture/pitfalls, concurrency, Xcode,
UI/design-system, accessibility, localization, simulator и performance rules.
Targets, schemes, compiler settings, tools, destinations и commands только
обнаруживать; не предполагать.

После requested fix lifecycle route заканчивается `verify ios ...`, но эта
read-only фаза сама verify не запускает.
