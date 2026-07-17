# Fresh verify: source observations and runtime gaps

## Наблюдения source

- `MyProfileView.swift` содержит
  `.accessibilityIdentifier("my-profile.symbol")` на стандартном SF Symbol
  `person.crop.circle.fill`.
- Экран содержит email, «Мои интервью», «Выход», disabled state, минимум
  `44pt` для кнопок, status text и Reduce Motion/Reduce Transparency branches.
- `MyProfileFeatureFactory.makeProfileView` владеет созданием internal store,
  container и view.
- `SysDevScenApp.swift` содержит `StubProfileSessionClient` и сценарную
  реализацию profile/history/logout внутри application target.

## Границы наблюдения

Свежий runtime подтвердил email, обе кнопки, count feedback, отсутствие
navigation, disabled empty state, history error и auth recovery. Сам SF Symbol
не был отдельным UI assertion, но его exact identifier и placement подтверждены
source inspection совместно с runtime открытием той же профильной view.

VoiceOver order/focus/announcements, maximum Dynamic Type, профильные light/dark
и increased-contrast варианты, Reduce Motion/Transparency, iPad layout,
hit-target geometry и older-OS/SDK fallback не наблюдались. Эти обязательства
имеют `UNKNOWN`.
