# Отчёт task-003 — focused tests и evidence mapping

## Итог

`task-003` выполнена. Добавлены focused unit/UI проверки для iOS app shell без
изменения production-кода, `.xcodeproj`, package contracts или shared product
артефактов. Тестовые файлы находятся внутри уже объявленных test targets, которые
подключаются проектом через filesystem-synchronized groups.

Unit-проверки фиксируют закрытый source contract `RootSection`: порядок cases,
начальное состояние `selectedSection`, связь `TabView(selection:)`, русские
labels, stable system images, accessibility identifiers и отсутствие Core Data
root ownership. Так как `RootSection` остаётся `private`, тесты не расширяют
production API ради testability.

UI-проверки запускают приложение и проверяют начальный выбор «Кейсы», наличие
трёх направлений «Кейсы», «Знания», «Профиль», перенос selected state между
разделами, повторный выбор активного раздела, постоянную navigation и отсутствие
шаблонных Core Data controls.

## Изменённые test paths

- `iOS/SysDevScen/SysDevScenTests/AppShellStateTests.swift`
- `iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift`
- `iOS/SysDevScen/SysDevScenTests/SysDevScenTests.swift` удалён как пустой
  template test.
- `iOS/SysDevScen/SysDevScenUITests/SysDevScenUITests.swift` удалён как пустой
  template UI/performance test.

`iOS/SysDevScen/SysDevScenUITests/SysDevScenUITestsLaunchTests.swift` оставлен
без изменений; он продолжает давать launch coverage в light/dark и orientation
configurations, которые запускает Xcode.

## Evidence route

`verification.md` не изменялся: initial Implement не имеет права писать этот
artifact. Сопоставление для будущей Verify-фазы подготовлено через этот отчёт:
командная проверка, unit contract checks, UI navigation/accessibility behavior,
application boundary и отсутствие template behavior собраны в
`evidence/task-003.md`.

## Выполненные проверки

Пакет перед записью тестов прошёл implement-валидацию.

```sh
python3 workflow/scripts/validate-platform-change.py --platform ios --feature app-shell --change app-shell --mode implement
```

Resolver контекста принял запечатанные инженерные области `application, ui` для
implement-фазы; набор правил не расширялся.

```sh
python3 workflow/scripts/find-platform-context.py --platform ios --feature app-shell --change app-shell --phase implement --scope application --scope ui
```

Scope baseline был создан coordinator до изменения тестовых путей; снимок
зафиксировал исходное состояние и стал контрольной границей для последующего
scope check после добавления тестов.

```sh
python3 workflow/scripts/validate-implementation-scope.py snapshot --platform ios --feature app-shell --change app-shell --task task-003 --baseline iOS/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-003.json
```

Первый запуск discovered command через watchdog дошёл до сборки, но остановился
на simulator clone launch с `NSMachErrorDomain Code=-308`, после чего watchdog
зафиксировал `no output progress for 120s`. Это не было compile failure.

```sh
bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 120 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' test
```

Recovery выполнен конечным override: тот же test command запущен с
`-parallel-testing-enabled NO`, чтобы Xcode не создавал нестабильный simulator
clone. Команда прошла через тот же watchdog budget и завершилась
`** TEST SUCCEEDED **`.

```sh
bash workflow/scripts/test-watchdog.sh --max-seconds 900 --stall-seconds 120 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -parallel-testing-enabled NO test
```

Итоговый successful test run выполнил 7 проверок XCTest для UI/launch и 3
проверки Swift Testing для unit-сценариев без failures. UI-набор проверил
запуск приложения, три видимые подписи, перенос выбранного состояния, повторный
выбор активного раздела и отсутствие шаблонных controls. Unit-набор проверил
закрытый source contract `RootSection` и отсутствие Core Data root interactions.

Проверка whitespace прошла без замечаний.

```sh
git diff --check -- iOS/SysDevScen/SysDevScenTests iOS/SysDevScen/SysDevScenUITests iOS/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-003.json
```

Scope check после test changes подтвердил, что изменения остались в разрешённых
границах задачи и baseline не подменялся.

```sh
python3 workflow/scripts/validate-implementation-scope.py check --platform ios --feature app-shell --change app-shell --task task-003 --baseline iOS/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-003.json --expected-sha256 <coordinator-held>
```

## Ограничения

`verification.md` остаётся read-only до отдельной Verify-фазы. Скриншоты и
`.xcresult` не копировались в package evidence, потому что scope task-003
разрешает только `evidence/task-003.md` и
`evidence/scope-baseline-task-003.json` среди package артефактов.
