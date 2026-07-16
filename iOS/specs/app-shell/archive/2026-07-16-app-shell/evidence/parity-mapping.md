# Evidence REQ-6 — parity mapping

Статус: PASS.

Общий продуктовый договор фиксирует одинаковые observable labels, порядок и
стартовый выбор для iOS и Android. iOS source содержит тот же порядок:
`case cases`, `case knowledge`, `case profile`; видимые строки — «Кейсы»,
«Знания», «Профиль»; initial selection — `.cases`.

iOS использует нативный `TabView`, что является допустимой платформенной формой
без изменения названий, порядка, стартового раздела или single-selection
семантики.
