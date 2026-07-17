# Verify evidence — native runtime — 20260717T112843Z

- Command: focused profile UI test on `iPhone 17`
- Result: `PASS`
- Observation: runtime наблюдал `pavel@example.com`, `my-profile.symbol`,
  `Мои интервью`, `Выход`, сообщение `Интервью: 3` и отсутствие navigation stack
  после нажатия на count feedback.

- Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B appearance light` and focused profile UI test
- Result: `PASS`
- Observation: профильная поверхность читается и сохраняет content semantics в
  light appearance.

- Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B appearance dark` and focused profile UI test
- Result: `PASS`
- Observation: профильная поверхность читается и сохраняет content semantics в
  dark appearance.

- Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B increase_contrast enabled` and focused profile UI test
- Result: `PASS`
- Observation: profile content, actions and count feedback остаются различимыми
  при повышенном контрасте.

- Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B content_size accessibility-extra-extra-extra-large` and focused profile UI test
- Result: `PASS`
- Observation: профильный runtime сохраняет email, symbol, actions and count
  feedback при максимальном проверенном Dynamic Type.

- Command: focused profile UI test on iPad mini `(A17 Pro)` device id `5A1F2D12-7633-4D9C-A7BE-AD5BD7690255`
- Result: `PASS`
- Observation: iPad mini runtime подтвердил профильную вкладку и content
  scenario; tab helper использовал резервный поиск по `label` и `identifier`,
  чтобы покрыть floating tab bar accessibility shape.

- Command: source and package presentation tests for visual environment branches
- Result: `PASS`
- Observation: presentation model tests закрывают Reduce Motion,
  Reduce Transparency и symbol fallback branches как deterministic native
  availability evidence.
