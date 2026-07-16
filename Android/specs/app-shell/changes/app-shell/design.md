# Design — app shell / Android / app-shell

## Current context

Обнаруженный Android graph содержит только `:app`; `MainActivity` показывает
сгенерированное Compose greeting и является единственной launch entry point.
Его Gradle file уже включает Compose и Material 3, а ресурсы сейчас содержат
только application name. Existing feature, navigation, data, network или
persistence boundaries, которые можно было бы переиспользовать, отсутствуют.

## Proposed architecture and boundaries

Proposed Gradle Android library module владеет цельной app-shell capability:
состоянием выбора, событиями выбора, публичной Compose UI-гранью, метаданными
направлений и нейтральными поверхностями. `:app` сохраняет lifecycle точки
входа, корневую композицию, конфигурацию и target resources; он зависит от
public seam и компонует его. Слой данных, domain, сеть, хранение,
DI framework и use-case layer не вводятся, потому что в этом increment нет
такого поведения.

## Modularity decision

- Outcome: isolated
- Capability triggers: independent-feature=yes; domain-data=no; network=no; persistence=no; reusable-ui=no; consumers=1; independent-ownership=yes
- Physical boundaries: Proposed Gradle Android library module for deterministic navigation capability isolation
- Public contracts and dependency direction: Публичный navigation composable принимает неизменяемое состояние выбранного раздела и callback выбора; state holder владеет правилами перехода; consumer code зависит от этого contract.
- App-shell responsibilities: entry-points, lifecycle, root-routing, dependency-wiring, platform-configuration, target-resources
- App-shell capability ownership: none
- Repository evidence: Android/settings.gradle.kts; Android/build.gradle.kts; Android/gradle/libs.versions.toml
- Rationale and trade-offs: Три постоянных направления, изменяемый выбор раздела и повторное использование визуальной структуры образуют цельную independently owned capability; separation защищает root composition и даёт deterministic state tests.
- Migration boundary and trigger: Миграция не требуется, потому что proposed physical boundary появляется до implementation; будущие дополнительные consumers сохраняют тот же public seam.
- Over-modularization check: Одна цельная navigation capability держит UI, состояние выбора и tests вместе; данные, сеть, storage и reusable design-system capability не выделяются, поэтому не создаётся лишняя build/API нагрузка.
- Boundary guard verdict: PASS

## Data and control flow

При запуске корневая композиция получает library UI seam. Держатель состояния
отдаёт утверждённый initial selection, принимает событие выбора направления,
валидирует его против фиксированного набора направлений и эмитит одно
неизменяемое новое состояние. Compose view отрисовывает navigation и
соответствующую нейтральную поверхность из этого состояния. Внешний контракт,
источник данных, cache, analytics event или сохранённое значение в этом path
не участвуют.

## Error and recovery model

Выбор локальный и synchronous, поэтому состояния загрузки, пустоты, offline,
retry и remote error states неприменимы. Activity recreation и изменения
конфигурации закрываются контрактом состояния, который можно восстановить или
реконструировать из утверждённого initial selection без придумывания
четвёртого состояния. Permission, intent, deep link, secret или
exported-component change не нужны.

## Platform UX trace and decisions

`platform-ux.md` имеет статус READY и выбирает Material 3 через обнаруженную
MaterialTheme dependency. Его semantic soft-blue роли выбора и фокуса, quiet
neutral surfaces, русские подписи из ресурсов, non-color selected cue,
масштабируемая typography и light/dark fallback направляют public composable.
M3 Expressive и Dynamic color остаются исключёнными до repository evidence;
accessible MaterialTheme soft-blue fallback поэтому входит в focused
verification.
Русское уточнение: это решение описывает нативную адаптацию визуального языка,
доступные состояния, ресурсные подписи и проверяемый fallback без расширения
продуктового поведения.

## Verification strategy

Plan создаёт deterministic state tests для начального и изменённого выбора,
Compose UI scenarios для подписей и selected semantics, проверки Gradle/module
boundary, а также focused runtime или inspection evidence для доступного
представления. Consumer integration собирает корневую композицию против
public seam; emulator-only claims остаются недоступными, пока discovered device
run не даст evidence.
Русское уточнение: стратегия проверки связывает состояние, композицию,
модульную границу и пользовательскую доступность с конкретными будущими
доказательствами.

## Applied engineering scopes

- application: Существующая точка входа остаётся composition-only и даёт discovered launch/lifecycle integration.
- compose: Существующая Compose support позволяет immutable state rendering, явные события выбора и deterministic composable scenarios.
- gradle: Settings и build scripts должны включить proposed physical library boundary через discovered plugins.
- localization: Фиксированные русские destination names переходят в resources, которыми владеет новая capability boundary, и сохраняют accessible naming.
- module: Independent selection capability изолируется в proposed Gradle Android library boundary с minimal public seam.
- ui: Material 3 navigation, нейтральные surfaces, semantics, font scale, appearance и non-color selected cues требуют focused presentation verification.
- Русское пояснение: выбранные области фиксируют ответственность, сборку,
  состояние, ресурсы и визуальную доступность без добавления данных, сети или
  хранения.
- Дополнительное русское пояснение: список областей нужен для реализации
  утверждённой оболочки, а не для расширения архитектуры за пределы текущего
  продуктового решения.
