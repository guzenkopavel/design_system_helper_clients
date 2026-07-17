# Доказательства задачи — task-004

## Итог

Recovery оставил `SysDevScen` только композицией потребителя для профиля:
`ContentView` и `RootView` принимают уже собранную `AnyView`, а создание
профильной поверхности выполняется через `MyProfileFeatureFactory.makeProfileView`
в корне композиции. Владение profile preview client и сценариями заглушки
перенесено в `MyProfileFeature`; оболочка приложения выбирает только общий
launch/runtime режим и не содержит `StubProfileSessionClient`, profile routes
или реализацию profile/history/logout fixture. Сборка потребителя, package tests
и focused app-shell/UI tests прошли успешно.

## Технические доказательства

iOS/SysDevScen/SysDevScen/ContentView.swift | modified | вкладка профиля принимает готовую `AnyView`
iOS/SysDevScen/SysDevScen/RootView.swift | modified | корневая маршрутизация больше не владеет состоянием профиля
iOS/SysDevScen/SysDevScen/SysDevScenApp.swift | modified | корень композиции вызывает `MyProfileFeatureFactory` без реализации profile fixture
iOS/SysDevScen/SysDevScenTests/AppShellStateTests.swift | modified | проверка границы оболочки обновлена под factory-owned surface
iOS/SysDevScen/SysDevScenUITests/MyProfileUITests.swift | modified | runtime проверяет видимый profile symbol, email, действия и count feedback
iOS/SysDevScen/SysDevScenUITests/AppShellUITests.swift | modified | tab helper устойчив к iPhone `TabBar` и iPad floating tab bar accessibility shape
iOS/MyProfileFeature/Package.swift | modified | `Resources` объявлены как SwiftPM resource
iOS/MyProfileFeature/Sources/MyProfileFeature/Data/MyProfilePreviewSessionClient.swift | added | profile preview client и fixture-сценарии принадлежат feature package

Command: `swift test --package-path iOS/MyProfileFeature`
Результат: PASS
Тесты: 16
Сбои: 0

Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 40000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenTests/AppShellStateTests test`
Результат: PASS
Тесты: 5
Сбои: 0

Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: PASS
Наблюдение: профильная вкладка показала `pavel@example.com`, `my-profile.symbol`,
`Мои интервью`, `Выход`, сообщение `Интервью: 3` и не открыла navigation stack.

Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 90 --max-output-lines 30000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'id=5A1F2D12-7633-4D9C-A7BE-AD5BD7690255' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: PASS
Наблюдение: тот же профильный сценарий прошёл на `iPad mini (A17 Pro)` с iOS
`26.5`; плавающая панель вкладок нашла вкладку профиля через резервный поиск по
`label` и `identifier`, после чего email, символ, действия, сообщение счётчика
и отсутствие навигационного стека совпали со сценарием iPhone.

Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B appearance light`
Результат: PASS
Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 20000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: PASS

Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B appearance dark`
Результат: PASS
Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 12000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: PASS

Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B increase_contrast enabled`
Результат: PASS
Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 12000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: PASS

Command: `xcrun simctl ui 2A5E6D88-4893-4154-AF8D-548EC14F6A4B content_size accessibility-extra-extra-extra-large`
Результат: PASS
Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 12000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: PASS

Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 12000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M5)' -parallel-testing-enabled NO -only-testing:SysDevScenUITests/MyProfileUITests/testProfileTabShowsContentAndCountFeedbackWithoutNavigation test`
Результат: UNKNOWN
Диагностика: первый iPad Pro destination дошёл до запуска runner, затем
`NSMachErrorDomain Code=-308` до выполнения теста. После этого тот же сценарий
успешно прошёл на `iPad mini (A17 Pro)`, поэтому device adaptation имеет
runtime-наблюдение на iPad, а `-308` сохранён как диагностика конкретного runner.

Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 600 --stall-seconds 90 --max-output-lines 60000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' -parallel-testing-enabled NO test`
Результат: PASS
Тесты: 18
Сбои: 0

После focused native runs iPhone simulator возвращён в нормальное состояние:
`appearance light`, `increase_contrast disabled`, `content_size large`.
