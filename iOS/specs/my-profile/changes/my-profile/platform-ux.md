# my-profile — iOS native UX

- **UX status:** `READY`
- **Platform:** `iOS`
- **Source product UX:** `specs/product/my-profile/ux.md`
- **Native design language adapter:** `Liquid Glass`
- **Color direction:** `soft blue`

## Evidence inspected

- `specs/product/my-profile/ux.md` задаёт shared intent, состояния, русские
  тексты, accessibility и quiet soft-blue направление.
- `iOS/SysDevScen/SysDevScen/ContentView.swift` показывает текущую вкладку
  профиля как заглушку `ContentUnavailableView`.
- `iOS/SysDevScen/SysDevScen.xcodeproj/project.pbxproj` задаёт iOS deployment
  target 26.0 для целевого приложения и включает генерацию локализованных строк.
- `iOS/AuthFeature/Package.swift` показывает существующий шаблон пакета Swift
  и нижнюю границу iOS 18.0 для пакета.
- `iOS/workflow/rules/ui-design-system.md` требует системный `Liquid Glass`,
  `standard components`, контроль `performance`, `Reduce Transparency`,
  `Reduce Motion`, `scrolling legibility` и `older-OS/SDK fallback` как нативные условия проверки,
  которые должны быть подтверждены отдельными сценариями.

## Shared intent mapping

Профильная вкладка остаётся спокойной служебной поверхностью. Крупный profile
symbol и email образуют идентификатор аккаунта, а блок действий разделяет
условное действие «Мои интервью» и критическое действие «Выход». Soft blue
semantic roles применяются к состоянию focus, информационному feedback и
доступному первичному действию; critical role выделяет выход без превращения
всего экрана в warning state.

## Information architecture and navigation

Экран живёт внутри существующей вкладки профиля и не создаёт вложенный
`navigation stack` для «Мои интервью», потому что продукт требует только краткое
сообщение. `Count message` остаётся кратким `native feedback`. Выход закрывает
`authenticated shell` через существующий маршрут восстановления авторизации и
возвращает пользователя к шагу `email entry`. `System navigation` остаётся поведением оболочки;
профильная поверхность не перехватывает его специально.

## Component and state mapping

- Profile symbol: стандартный SF Symbols account/profile marker с декоративной
  семантикой доступности.
- Email text: читаемый идентификатор аккаунта и accessible value для текущего
  профиля.
- Action group: `standard components` и `functional controls`; «Мои интервью»
  имеет состояния загрузки `loading`, доступности `enabled`, `disabled` и `error-blocked`,
  а пользователь видит результат через состояние кнопки.
- Count feedback: краткий `native transient feedback` с `assistive announcement`,
  чтобы сообщение было заметно визуально и доступно ассистивно.
- Logout: standard destructive/critical action с блокировкой на время loading и
  восстановимым сообщением о сбое.

## Native visual language

`Liquid Glass` используется только в `functional controls` и `navigation-adjacent`
`surface treatment`, если `SDK availability` и поведение системных компонентов
это подтвердят в текущем окружении. `Content background` остаётся `quiet neutral`,
чтобы email и состояние истории сохраняли `scrolling legibility`. `Custom glass effects`
не создаются; предпочитаются `standard components`. Если `Liquid Glass` недоступен
или снижает `legibility/performance`, `fallback` использует обычные `system materials`
и `semantic roles` без изменения `product outcome`.

## Color roles and appearance

`Soft blue` применяется через `semantic roles`: информационный `accent`, `focus`
и `primary interactive affordance` для доступного действия. `Critical action`
использует системную `destructive/critical` роль. `Disabled state` различим через
`traits`, `reduced emphasis`, отсутствие `action affordance` и текстовое или
семантическое состояние, а не только цвет. `Light`, `dark` и `increased contrast`
проверяются отдельно.

## Accessibility and localization

`VoiceOver order`: `profile symbol` не дублирует email; email объявляется как
текущий email профиля; «Мои интервью» объявляет доступность или недоступность.
`Count message` и `logout loading` объявляются отдельным ассистивным сообщением.
`Dynamic Type` должен сохранять читаемость email и кнопок без `clipping`.
Минимальный `hit target` — 44×44pt. Русские строки не собираются из
грамматически зависимых `fragments`; будущая локализация должна использовать
найденный механизм проекта.

## Motion and interaction

Reduce Motion отключает необязательные переходы и оставляет мгновенную смену
state. Reduce Transparency отключает или упрощает glass/material treatment без
потери контраста. Повторные taps во время loading игнорируются или блокируются
на уровне state, а cancellation пагинации при уходе с экрана не должна создавать
позднее объявление stale count.

## Device and layout adaptation

`Layout` центрирует `profile symbol` и email в верхней части, но сохраняет
`scroll` или `flexible vertical spacing` для длинного email и `Dynamic Type`.
iPhone и iPad используют одинаковый порядок контента; `wide layout` может
увеличить `breathing space`, но не добавляет новую поверхность и не меняет
сценарий. `Increased contrast` и `larger text` имеют приоритет над декоративной плотностью.

## Fallback and availability

`Availability` не предполагается по названию Xcode или SDK. При недоступности
`Liquid Glass`, `older-OS/SDK fallback` использует `standard components`,
`system backgrounds` и `semantic roles` без изменения результата. При включённом
`Reduce Transparency` `fallback` становится обязательным. При `Reduce Motion`
`count feedback` и `logout transition` остаются без существенной анимации.

## Verification scenarios

- `NATIVE-APPEARANCE`: базовая профильная поверхность с содержимым, пустой
  историей и состоянием выполнения выхода.
- `NATIVE-LIGHT`: читаемость email, действий и сообщения в light appearance.
- `NATIVE-DARK`: читаемость email, действий и сообщения в dark appearance.
- `NATIVE-INCREASED-CONTRAST`: контраст и нецветовые признаки non-color state cues.
- `NATIVE-ASSISTIVE-SEMANTICS`: VoiceOver labels, traits, value и announcements с русским смыслом и правильным порядком.
- `NATIVE-TEXT-SCALING`: самый крупный поддержанный Dynamic Type без clipping.
- `NATIVE-MOTION`: поведение Reduce Motion для сообщения и переходов.
- `NATIVE-DEVICE-ADAPTATION`: порядок layout и целевые зоны hit targets на iPhone и iPad.
- `NATIVE-AVAILABILITY-FALLBACK`: fallback Liquid Glass для older-OS/SDK или
  Reduce Transparency с сохранением поведения.

## Open gaps

None.
