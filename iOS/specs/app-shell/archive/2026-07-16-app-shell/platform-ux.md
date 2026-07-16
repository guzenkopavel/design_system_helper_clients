# iOS platform UX — app shell

- **UX status:** `READY`
- **Platform:** `iOS`
- **Source product UX:** `specs/product/app-shell/ux.md`
- **Native design language adapter:** `Liquid Glass`
- **Color direction:** `soft blue`

## Evidence inspected

Общий intent и наблюдаемые ограничения прочитаны из
`specs/product/app-shell/spec.md` и `specs/product/app-shell/ux.md`. Пакет iOS
выбирает `application` и `ui` в `meta.json`; `implementation-spec.md` указывает
`SysDevScenApp` и `ContentView` как текущий путь композиции.

`iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj` объявляет deployment
target `26.5`, `SDKROOT = auto`, Swift 5.0, asset `AccentColor` и targets
`SysDevScen`, `SysDevScenTests`, `SysDevScenUITests`. Local discovery сообщает
Xcode 26.5 и iPhoneSimulator SDK 26.5. Реальный корень — SwiftUI `WindowGroup`
в `SysDevScenApp.swift`; `ContentView.swift` — технический шаблон `Core Data`.
Слой дизайн-токенов, готовый навигационный примитив и существующее оформление
`Liquid Glass` не обнаружены. Поэтому артефакт выбирает системные стандартные
components и semantic roles, а не выдуманные имена токенов или API.

Контрольные термины адаптера: `Liquid Glass`, `functional controls`,
`navigation`, `content background`, `soft blue`, `semantic roles`, `light`,
`dark`, `increased contrast`, `Reduce Transparency`, `Reduce Motion`,
`scrolling legibility`, `standard components`, `performance`,
`older-OS/SDK fallback`.

## Shared intent mapping

Спокойное направление `soft blue` мапится на iOS semantic roles: выбранная
navigation, informational accent, focus, primary text и quiet neutral surface.
Оттенок может выделять выбранное или информационное состояние, но не передаёт
выбор, фокус, доступность или ошибку в одиночку. Стандартная типографика,
форма индикатора и accessibility-selected semantics усиливают состояние. Три
русские labels, фиксированный порядок, начальный выбор «Кейсы» и правило одного
выбранного раздела не меняются.

## Information architecture and navigation

Корень приложения даёт один постоянный нативный navigation control с ровно
«Кейсы», «Знания», «Профиль» в этом порядке. Он открывает «Кейсы» первым; выбор
item меняет нейтральную базовую поверхность на месте и переносит единственное
selected state. Повторный выбор активного item сохраняет surface и не создаёт
nested route или history. Navigation остаётся доступной на каждой поверхности,
а поверхности показывают только смысл раздела: без fabricated content, data,
loading, error, account или network state.

## Component and state mapping

Implementation использует найденный SwiftUI-корень и standard components для
functional controls и navigation. Единственный владелец состояния хранит
selected section; controls отправляют действия выбора и раскрывают русскую
подпись, роль и selected state для assistive technologies. Перед добавлением
оформления implementation проверяет стандартные extension points и
`AccentColor`. Нельзя вводить локальные литералы цвета, шрифта и отступов,
custom glass effects или reusable primitive без отдельно доказанной потребности
и consumers.

Применимые состояния: default, selected, pressed/focused, disabled только при
реальной недоступности, и content overflow. Loading, empty, error, offline и
recovery не применимы, потому что increment не имеет data или operation,
которые могли бы их создать. Selected и focus states сохраняют non-color cues и
не должны делать доступные направления похожими на disabled.

## Native visual language

`Liquid Glass` является system-first и conditional. Если установленный SDK даёт
standard availability-checked treatment для выбранных navigation/control, его
можно использовать только на этих functional controls и navigation. Это не
content background, не декоративная заливка страницы и не custom effect.
Нейтральные поверхности остаются читаемыми при прокрутке рядом с navigation;
glass используется сдержанно, не конкурирует с section name, не скрывает
content и не добавляет лишнюю rendering performance cost.

Implementation должен проверить точный SDK symbol, signature и availability до
использования; package намеренно не предписывает API name. Standard SwiftUI
components остаются источником истины, а собственная визуальная имитация не
создаётся.

## Color roles and appearance

Существующий `AccentColor` доказывает только акцент приложения, а не полную
систему токенов. Реализация мапит `soft blue` на семантический акцент выбора
или информации через найденный asset либо подтверждённое расширение
дизайн-системы. Для нейтральных поверхностей, текста, фокуса и disabled states
используются системные semantic foreground/background и selection treatments;
локальное feature styling запрещено.

В `light` и `dark` внешний вид текста и индикатора выбора сохраняет contrast и
нецветовое различие. В `increased contrast` системные adaptations и non-color
selected/focus cues остаются intact; selected accent не усиливается и не
инвертируется вслепую. В **Reduce Transparency** navigation/control использует
системный opaque или less-transparent material result, сохраняя hierarchy и
selected state вместо blur simulation. `content background` не становится glass
ни в одном appearance.

## Accessibility and localization

Visible и accessible names совпадают с русскими строками: «Кейсы», «Знания»,
«Профиль». Каждый navigation control раскрывает role и selected semantic state;
визуальный индикатор выбора и emphasis дают redundant non-color cue. `VoiceOver`
идёт по постоянному порядку навигации, затем по активной поверхности.
`Dynamic Type` должен сохранять полную подпись каждого destination, current
selection и доступ ко всем destinations; overflow решается adaptive standard
layout, а не обрезанием, которое теряет label или state. Light, dark и
increased-contrast appearance являются обязательными checks. Будущая
localization может заменить resources, но должна сохранить meaning label,
order, accessible-name parity и single selection.

## Motion and interaction

Отклик на выбор должен быть немедленным и сдержанным. Стандартное движение
control/navigation, если оно поставляется найденным component, является только
улучшением и не становится единственным сигналом выбора. При **Reduce Motion**
implementation использует системно уменьшенное поведение или убирает лишнее
переходное движение, сохраняя немедленное изменение состояния и объявление
доступности. Loading, destructive confirmation, haptic requirement и artificial
animation не добавляются.

## Device and layout adaptation

iOS deployment target — 26.5; target поддерживает iPhone и iPad families.
Первая implementation проверяет compact и wider layouts с той же постоянной
семантикой навигации. Adaptive standard navigation presentation можно выбрать
только после подтверждения в installed SDK; нельзя менять три labels, их order,
initial selection, availability или single-selection rule. Scrolling должен
сохранять читаемость активной поверхности и видимость функциональной навигации,
не размещая glass behind page content.

## Fallback and availability

Обнаруженные deployment и SDK равны 26.5, но это не доказывает доступность
конкретного `Liquid Glass` API в каждом component или future build configuration.
До integration implementation подтверждает API availability в installed SDK и
закрывает его appropriate platform availability check. Для **older-OS/SDK
fallback** или когда API/component unavailable, shell использует то же
стандартное непрозрачное семантическое оформление SwiftUI navigation and control:
спокойные нейтральные поверхности, семантический soft-blue accent выбора,
нецветовые признаки selected/focus, Dynamic Type и accessibility-selected state.
Fallback сохраняет shared behavior, оставляет поведение для пользователя тем же
и не имитирует Liquid Glass через custom blur, materials или effects.

## Verification scenarios

- Launch проверяет выбранные «Кейсы» и ровно три постоянных направления в
  требуемом порядке; каждый выбор и повторный выбор сохраняет общий договор
  навигации без искусственных вторичных состояний.
- Simulator/UI inspection проверяет видимые подписи, role для VoiceOver,
  выбранную семантику, порядок фокуса, нецветовые признаки выбора,
  `Dynamic Type` и поведение при переполнении content.
- Визуальная проверка охватывает спокойные нейтральные поверхности,
  семантический `soft blue`, типографику, hit areas и scrolling legibility в
  light, dark и increased contrast, включая **Reduce Transparency**.
- Проверка взаимодействия подтверждает немедленный выбор и **Reduce Motion** без
  ситуации, где движение является единственным сигналом.
- Когда availability-checked Liquid Glass standard treatment интегрирован,
  simulator evidence покрывает его; older-OS/SDK fallback отдельно собирается
  или записывается как unavailable, если installed environment не может его
  выполнить. Unavailable API не считается рабочим по предположению.

## Open gaps

None.
