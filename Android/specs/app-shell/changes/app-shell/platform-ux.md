# Android platform UX — app shell

- UX status: READY
- Platform: Android
- Source product UX: specs/product/app-shell/ux.md
- Native design language adapter: Material 3
- Color direction: soft blue

## Evidence inspected

`Android/app/build.gradle.kts` подтверждает Compose, Compose BOM и Material 3;
`Android/gradle/libs.versions.toml` содержит эти зависимости; текущая точка
входа является Compose `ComponentActivity`. В repository нет evidence для
M3 Expressive APIs, Android 12+ Dynamic color decision, существующих custom
tokens или reusable navigation component. Это repository
SDK/dependency/product evidence выбирает только устойчивый Material 3 baseline.
Русское уточнение: решение основано на текущем составе проекта и не делает
выводов о недоказанных компонентах или персонализации.

## Shared intent mapping

Общий спокойный soft-blue direction переводится в выбор, primary action и
focus через semantic tonal roles на quiet neutral surfaces. Material 3 color
roles должны давать accessible on-colors; typography и shapes формируют
иерархию, а selected state остаётся понятным без опоры только на color accent.
Русское уточнение: выбранность должна восприниматься и визуально, и
ассистивно, при этом спокойный синий остаётся семантическим акцентом.

## Information architecture and navigation

Один persistent navigation control показывает три утверждённых направления в
общем порядке. Initial destination совпадает с shared first selection; выбор
другого направления обновляет одну in-place neutral surface без extra
destination, fabricated content, back-stack growth, account state или
network-dependent state.
Русское уточнение: навигация показывает только утверждённые направления и не
создаёт вымышленные данные, состояния аккаунта или сетевую зависимость.

## Component and state mapping

Material 3 navigation components показывают подписи направлений и selected
state. Один владелец состояния предоставляет immutable selected-section state
и принимает события выбора; каждая neutral surface показывает только смысл
своего направления. Public UI seam позволяет deterministic state и Compose
tests.
Русское уточнение: состояние выбора остаётся явным, проверяемым и отделённым
от корневой точки входа приложения.

## Native visual language

MaterialTheme задаёт Material 3 color, typography и shapes вместо feature-local
literal styling. Оболочка выбирает quiet neutral surfaces, спокойную
information hierarchy и умеренный selected emphasis. M3 Expressive не выбран,
потому что repository SDK/dependency/product evidence не доказывает его
доступность или необходимость для этой небольшой foundational surface.
Русское уточнение: визуальная система остаётся сдержанной, нативной и
проверяемой через уже доступные зависимости.

## Color roles and appearance

Soft blue является semantic selection и informational accent, но никогда не
единственным признаком выбора. MaterialTheme задаёт semantic tonal roles и
accessible on-colors для light и dark appearance; emphasis, indicator shape и
selected semantics усиливают состояние. Dynamic color не включается: нет
product/platform decision или repository API evidence для Android 12+
personalization path, поэтому accessible soft-blue fallback остаётся
authoritative.
Русское уточнение: цветовое решение должно работать одинаково понятно в
светлом и тёмном оформлении без персонализации.
Дополнительное русское уточнение: выбранный цветовой подход должен оставаться
семантическим, проверяемым и доступным для пользователя при любом оформлении.

## Accessibility and localization

Resource-backed Russian labels совпадают с видимыми и accessible names. Каждый
destination раскрывает role, selected state и non-color visual cue; focus order
следует persistent navigation order. Typography должна выдерживать font
scaling, а layout должен сохранять labels discoverable в light, dark и
increased-contrast appearances.
Русское уточнение: подписи и выбранность должны оставаться читаемыми,
озвучиваемыми и различимыми при увеличенном тексте.
Дополнительное русское уточнение: доступность важнее декоративной формы, поэтому
каждое направление должно быть понятно без знания внутренней реализации.

## Motion and interaction

Выбор даёт immediate и restrained Material 3 feedback без loading transition,
destructive confirmation или simulated data. Повторный выбор текущего
destination сохраняет его surface. Motion, если его даёт standard component,
не становится единственным носителем состояния и учитывает platform
reduced-motion behavior там, где он доступен.
Русское уточнение: взаимодействие остаётся мгновенным и спокойным, а состояние
не зависит от одной анимации.

## Device and layout adaptation

Первая реализация проверяет compact phone layout и читаемость labels при
increased font scale. Wider layouts могут использовать те же persistent
navigation semantics без изменения destination order, names или
single-selection behavior; unverified adaptive component не предписывается.
Русское уточнение: адаптация размеров не меняет общий порядок, смысл
направлений и правило единственного выбора.

## Fallback and availability

Material 3 доступен через обнаруженную dependency. M3 Expressive исключён до
repository SDK/dependency/product evidence. Dynamic color исключён даже там,
где Android 12+ мог бы его поддержать; это сохраняет MaterialTheme soft-blue
fallback и accessible on-colors во всех appearance.

## Verification scenarios

Проверить first launch, selection каждого destination, repeated selection,
ровно один selected item, resource labels, Compose semantics,
TalkBack-relevant state, font scaling, light/dark appearance, increased
contrast там, где runtime его предоставляет, и semantic soft-blue fallback.
Отсутствующая emulator capability записывается как unavailable runtime
evidence, а не inferred success.
Русское уточнение: сценарии проверки должны отличать реальные результаты от
недоступной среды и сохранять честный статус evidence.
Дополнительное русское уточнение: проверяющий фиксирует только наблюдаемое
поведение и не засчитывает предположения как успешный результат.

## Open gaps

None.
