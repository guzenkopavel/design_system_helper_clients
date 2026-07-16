# Evidence REQ-2 — первый запуск и начальный выбор

Статус: PASS.

Fresh command `xcodebuild ... -parallel-testing-enabled NO test` прошла через
`test-watchdog.sh` и завершилась `** TEST SUCCEEDED **`. UI test
`testLaunchShowsCasesFirstAndKeepsNavigationAvailable` запустил приложение на
`iPhone 17 Pro`, нашёл tabs «Кейсы», «Знания», «Профиль» и подтвердил, что
`Кейсы` выбран, а остальные tabs не выбраны.

Unit test `rootSectionContractStaysClosedAndOrdered` дополнительно подтвердил
source contract `@State private var selectedSection: RootSection = .cases`.
