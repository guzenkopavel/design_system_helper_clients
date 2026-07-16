# task-003 — доказательства

## Итог

Задача выполнена. В модуле `Android/app-shell` добавлена оболочка Material 3 с
поднятым состоянием, русскими ресурсными подписями, нейтральными поверхностями
для трёх утверждённых направлений и запасным спокойным синим оформлением для
светлого и тёмного режима. Dynamic color не включён, потому что
`platform-ux.md` не содержит подтверждения на уровне repository
SDK/dependency/product evidence для такого решения.

## RED

Команда:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 360 -- ./Android/gradlew -p Android --no-daemon :app-shell:compileDebugAndroidTestKotlin --console=plain
```

Результат: `BUILD FAILED`. Тестовый исходник `AppShellTest.kt` не смог
скомпилироваться из-за `Unresolved reference 'AppShell'`, что подтвердило
отсутствие публичной UI-границы до реализации.

## GREEN

Команда компиляции основного кода и тестового androidTest исходника:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 700 -- ./Android/gradlew -p Android --no-daemon :app-shell:compileDebugKotlin :app-shell:compileDebugAndroidTestKotlin --console=plain
```

Результат: `BUILD SUCCESSFUL`.

Команда статической проверки ресурсов:

```text
rtk python3 - <<'PY'
from pathlib import Path
import re
...
PY
```

Результат: `STATIC_CHECKS_PASS`. Проверка подтвердила порядок русских подписей
`Кейсы`, `Знания`, `Профиль`, строки semantics `Выбрано` и `Не выбрано`,
нейтральные тексты поверхностей, отсутствие affordances для loading, error,
account и data, а также достаточную контрастность пар soft-blue/on-colors:

- light primary/onPrimary: `6.44`;
- light primaryContainer/onPrimaryContainer: `10.41`;
- light surface/onSurface: `16.63`;
- dark primary/onPrimary: `7.74`;
- dark primaryContainer/onPrimaryContainer: `7.48`;
- dark surface/onSurface: `14.41`.

## Runtime evidence

Команда:

```text
rtk bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 120 --max-output-lines 900 -- ./Android/gradlew -p Android --no-daemon :app-shell:connectedDebugAndroidTest --console=plain
```

Результат: `UNKNOWN` для покрытия на runtime/emulator. Gradle собрал androidTest
APK, но `connectedDebugAndroidTest` завершился ошибкой
`DeviceException: No connected devices!`. Поэтому emulator, поведение TalkBack
и доступность, проверяемая только на runtime, не засчитаны как `PASS`.

## Проверенные контракты

- `Compose state`: `AppShell` принимает `AppShellState` и callback
  `onDestinationSelected`, не владеет внешним состоянием и передаёт события
  выбора наверх.
- `localization`: видимые подписи направлений и строки состояния выбранности
  хранятся в `strings.xml`.
- `accessibility`: выбранность передаётся через `stateDescription`, а также
  поддержана нецветовым маркером `●`/`○`.
- `design-system`: интерфейс построен на `MaterialTheme`, `Scaffold`,
  `NavigationBar`, `NavigationBarItem`, `Surface`, типографике и семантических
  цветовых ролях.
- `platform-ux.md`: реализация следует базовому Material 3, спокойному синему
  направлению и запрету вымышленного содержимого.
- `Material 3`: использованы только доступные Material 3 компоненты из текущего
  Gradle graph.
- `light/dark`: заданы отдельные цветовые схемы для светлого и тёмного режима.
- `accessible on-colors`: host-проверка контраста для primary,
  primaryContainer и surface пар в светлом и тёмном оформлении не ниже `4.5`.
- `dynamic color`: не включён из-за отсутствия подтверждённого решения и
  repository evidence.
- `soft-blue fallback`: ресурсы спокойного синего являются authoritative
  fallback для светлого и тёмного appearance.
- `emulator`: устройство или эмулятор не подключены, поэтому runtime часть
  честно отмечена как `UNKNOWN`.

## Граница изменений

Команда:

```text
rtk python3 workflow/scripts/validate-implementation-scope.py check --platform android --feature app-shell --change app-shell --task task-003 --baseline Android/specs/app-shell/changes/app-shell/evidence/scope-baseline-task-003.json --expected-sha256 coordinator-held-token
```

Результат: `Implementation scope: VALID (check)`.
