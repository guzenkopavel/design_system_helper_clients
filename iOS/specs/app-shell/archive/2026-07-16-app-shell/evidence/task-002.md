# Отчёт task-002 — нативная SwiftUI shell-поверхность

## Итог

`task-002` выполнена. Корневая shell-поверхность реализована в файле
`iOS/SysDevScen/SysDevScen/ContentView.swift` через системный SwiftUI
`TabView(selection:)`. Закрытый `RootSection` задаёт ровно три раздела, а
единственный локальный владелец выбора хранится в
`@State private var selectedSection: RootSection = .cases`.

Направления отображаются в порядке «Кейсы», «Знания», «Профиль». Начальный
выбор — «Кейсы». Повторный выбор активной вкладки не создаёт дополнительный
маршрут, историю или второго владельца состояния. Поверхности нейтральные и
показывают только смысл раздела через системный `ContentUnavailableView`, без
фиктивного контента, данных, сети, хранения, аналитики или состояния аккаунта.

## Изменённые production paths

- `iOS/SysDevScen/SysDevScen/ContentView.swift`

`iOS/SysDevScen/SysDevScen/Assets.xcassets` не изменялся: задача не потребовала
новых ресурсов, а визуальное направление покрыто системными семантическими
ролями и текущим fallback для accent.

## UX и accessibility

`platform-ux.md` использован как read-only contract context. `Liquid Glass` не
интегрирован: точные SDK symbol/signature и availability не выбирались в рамках
этой задачи, поэтому применён системный SwiftUI fallback без самодельного blur,
material, glass simulation или декоративного `content background`.

Видимые и доступные имена берутся из одного `section.title`: «Кейсы», «Знания»,
«Профиль». Системный `TabView` отвечает за нативную роль навигации, hit areas,
selected semantics и системную обработку фокуса. Выбранное состояние различимо
не только цветом: simulator screenshots показывают системную selected pill,
иконку и усиление label.

Для Reduce Motion и Reduce Transparency в коде нет самодельной анимации, явного
перехода, custom material, blur или glass effect; поэтому поведение остаётся
системным fallback стандартных controls. Для light/dark, increased contrast и
Dynamic Type выполнена simulator-проверка.

## Выполненные проверки

Пакет перед записью кода прошёл implement-валидацию.

```sh
python3 workflow/scripts/validate-platform-change.py --platform ios --feature app-shell --change app-shell --mode implement
```

Resolver контекста успешно принял запечатанные инженерные области
`application, ui` для implement-фазы; это подтвердило, что набор правил не
расширялся и соответствует текущему package.

```sh
python3 workflow/scripts/find-platform-context.py --platform ios --feature app-shell --change app-shell --phase implement --scope application --scope ui
```

Scope baseline был успешно создан coordinator до production writes; этот
снимок использован как контрольная граница, чтобы последующая проверка
подтвердила отсутствие посторонних изменений.

```sh
python3 workflow/scripts/validate-implementation-scope.py snapshot --platform ios --feature app-shell --change app-shell --task task-002 --baseline iOS/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-002.json
```

Статическая проверка не нашла Core Data template interactions в корневом пути.

```sh
rg -n "CoreData|managedObjectContext|@FetchRequest|PersistenceController|\\bItem\\b|addItem|deleteItems|NavigationLink|EditButton|Select an item|Add Item" iOS/SysDevScen/SysDevScen/ContentView.swift iOS/SysDevScen/SysDevScen/SysDevScenApp.swift
```

Статическая проверка не нашла локального styling, motion или
transparency/glass simulation в новой поверхности.

```sh
rg -n "\\.background\\(|\\.foregroundStyle\\(|Color\\(|Font\\(|\\.font\\(|\\.padding\\(|\\.animation\\(|withAnimation|material|blur|glass|Material" iOS/SysDevScen/SysDevScen/ContentView.swift
```

Проверка whitespace прошла без замечаний.

```sh
git diff --check -- iOS/SysDevScen/SysDevScen/ContentView.swift iOS/SysDevScen/SysDevScen/Assets.xcassets
```

Сборка под simulator прошла через watchdog, результат `** BUILD SUCCEEDED **`.

```sh
bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 120 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' build
```

Simulator runtime-проверка установила и запустила приложение на `iPhone 17 Pro`
`6614DDB0-6F00-476C-A132-F11506A87A8B`. Временные screenshots для light/dark
сохранены в `/tmp/app-shell-task-002-dark.png` и
`/tmp/app-shell-task-002-light.png`.

```sh
bash workflow/scripts/test-watchdog.sh --max-seconds 1200 --stall-seconds 180 --max-output-lines 30000 -- zsh -lc '<boot/install/launch/screenshot light/dark>'
```

Отдельная simulator-проверка включила increased contrast и крупный Dynamic
Type, сделала screenshot `/tmp/app-shell-task-002-contrast-dynamic-type.png`,
затем вернула настройки simulator к `increase_contrast disabled` и
`content_size large`.

```sh
bash workflow/scripts/test-watchdog.sh --max-seconds 1200 --stall-seconds 180 --max-output-lines 30000 -- zsh -lc '<increase_contrast/content_size/screenshot/restore>'
```

Scope check после production writes подтвердил, что изменения остались в
разрешённых границах задачи и baseline не подменялся.

```sh
python3 workflow/scripts/validate-implementation-scope.py check --platform ios --feature app-shell --change app-shell --task task-002 --baseline iOS/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-002.json --expected-sha256 <coordinator-held>
```

## Ограничения

Отдельные UI/unit tests не добавлялись: они принадлежат `task-003`. Скриншоты
не копировались в package evidence, потому что scope task-002 разрешает только
`evidence/task-002.md` и `evidence/scope-baseline-task-002.json` среди package
артефактов.
