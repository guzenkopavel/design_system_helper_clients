# Implementation spec — app shell / Android / app-shell

## Intake reference

Реализация следует утверждённому shared product contract в
`specs/product/app-shell/spec.md`. Платформа может адаптировать нативную форму
interaction, но не меняет shared observable behavior.

## Shared contract references

`REQ-1`–`REQ-6` и `AC-1`–`AC-5` трассируются в `verification.md`. Они остаются
владением shared specification, не переопределяются в Android package и не
ослабляются platform-решениями.

## Platform requirements

### AND-REQ-1 — Изолированная Android-возможность оболочки

Предоставить UI оболочки, состояние выбора, фиксированные подписи и
нейтральные поверхности направлений через proposed Android library boundary с
минимальным публичным Compose-контрактом. Существующая точка входа только
компонует этот контракт и сохраняет ответственность за lifecycle/root
integration.

### AND-REQ-2 — Нативное доступное представление навигации

Отрисовать три утверждённых направления через Material 3 semantics, видимые
non-color признаки выбора, масштабируемый текст, русские подписи из ресурсов и
поведение светлого/тёмного оформления, согласованные с `platform-ux.md`.

## Platform acceptance criteria

### AND-AC-1 — Граница и композиция собираются

Обнаруженный Gradle graph включает proposed library boundary, не раскрывает
implementation details за пределы public Compose seam и позволяет существующей
точке входа компоновать shell без dependency cycle.

Covers: AND-REQ-1

### AND-AC-2 — Состояние и UI-сценарии наблюдаемы

Focused deterministic state и Compose UI scenarios наблюдают первый выбор,
выбор каждого утверждённого направления, ровно один выбранный элемент, подписи
и доступную selected semantics на публичной поверхности.

Covers: AND-REQ-1, AND-REQ-2

### AND-AC-3 — Нативный визуальный и accessibility fallback сохранён

Focused runtime или inspection evidence покрывает Material 3 light/dark
appearance, soft-blue semantic fallback, масштабирование шрифта,
TalkBack-relevant labels и selected state без опоры только на color.
Русское уточнение: проверка должна подтвердить доступность, визуальную
понятность выбранного состояния и сохранение утверждённого поведения без
добавления новых продуктовых возможностей.

Covers: AND-REQ-2

## Constraints

Общие подписи, порядок, initial selection и no-content boundaries остаются
неизменными. Используются только обнаруженные Compose и Material 3
dependencies; нельзя предполагать emulator, M3 Expressive API, Dynamic color,
DI framework или хранение.

## Integration points

`Android/settings.gradle.kts` сейчас включает только `:app`, а
`Android/app/build.gradle.kts` содержит существующие Compose и Material 3
dependencies. Новая library boundary должна быть включена в этот Gradle graph
и скомпонована из `MainActivity` без переноса capability logic в application
module.

## Open questions

None.
