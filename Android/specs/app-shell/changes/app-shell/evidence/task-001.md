# Evidence — task-001

## Результат

Задача `task-001` выполнена: создана физическая Gradle Android library boundary
для `:app-shell`, подключена к обнаруженному Android project graph и оставлена
без продуктового поведения. Модуль содержит только минимальный Gradle build
file и manifest, поэтому состояние выбора, Material 3 UI и wiring приложения
остаются задачами следующих шагов.

## Изменённые task paths

- `Android/settings.gradle.kts` включает `:app-shell`.
- `Android/build.gradle.kts` объявляет `android-library` plugin alias на root
  level, чтобы общий граф сборки мог подключать библиотечный модуль через
  найденный каталог версий.
- `Android/gradle/libs.versions.toml` добавляет plugin alias
  `android-library` для нативного Android library plugin и будущего
  подключения отдельной границы оболочки.
- `Android/app-shell/build.gradle.kts` создаёт Android library module с теми же
  обнаруженными SDK baseline, Compose enablement и Material 3 dependencies,
  сохраняя единый уровень компиляции и минимальную конфигурацию.
- `Android/app-shell/src/main/AndroidManifest.xml` добавляет минимальный
  library manifest без exported components и без новых точек входа.

## Focused checks

- RED diagnostic: до wiring `:app-shell` отсутствовал в discovered project
  graph, что подтверждало отсутствие нужной физической границы.
- Project graph check: `rtk bash workflow/scripts/test-watchdog.sh
  --max-seconds 300 --stall-seconds 60 --max-output-lines 1200 --
  ./Android/gradlew -p Android projects --console=plain` завершился успешно и
  показал `Project ':app-shell'`.
- Первый module build через daemon остановился watchdog по stall на
  `:app-shell:extractDebugAnnotations`; Gradle exception не было. Повтор с
  увеличенным конечным stall budget воспроизвёл тот же daemon stall.
- Диагностический bounded build без reuse daemon:
  `rtk bash workflow/scripts/test-watchdog.sh --max-seconds 420
  --stall-seconds 180 --max-output-lines 3000 -- ./Android/gradlew -p Android
  --no-daemon :app-shell:assembleDebug --stacktrace --console=plain`
  завершился `BUILD SUCCESSFUL in 14s`.

## Scope and boundary evidence

Проверены markers `Gradle task`, `module boundary`, `module build`,
`public contract`, `consumer integration`, `dependency graph` и
`app-shell wiring`. В рамках этой задачи `:app` не получил состояние,
навигацию, UI или зависимость на новый модуль; он остаётся будущим consumer для
следующих задач. Производственная запись ограничена task-declared paths.

Из-за параллельных iOS/harness изменений в общем worktree scope baseline был
переснят на текущем фоне после подтверждения, что Android production writes
ограничены task paths. SHA token baseline не записан в evidence.
