# Fresh verification: build, graph and boundaries

## Consumer build

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 40000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' build`
- Destination: `iPhone 17`, iOS Simulator `26.5`, arm64
- Exit status: `0`
- Result: `PASS`
- Duration: `5.49s`
- Observation: Xcode построил consumer `SysDevScen`; граф содержит `SysDevScen -> MyProfileFeature -> AuthFeature`, итог `BUILD SUCCEEDED`.

## Physical graph

- Commands: `swift package --package-path iOS/MyProfileFeature describe --type json`; `swift package --package-path iOS/MyProfileFeature show-dependencies --format json`
- Result: `PASS`
- Observation: обнаружен отдельный library product/target `MyProfileFeature`, отдельный test target и единственная package dependency на `AuthFeature`; цикл не обнаружен.

## Public API and visibility

- Command: `rg -n '^public (struct|final class|protocol|enum)|^    public (init|func|let|private\\(set\\) var)' iOS/MyProfileFeature/Sources/MyProfileFeature`
- Result: `FAIL`
- Observation: consumer получает поверхность не через фабрику: `ContentView.swift` напрямую создаёт `MyProfileView`, а factory создаёт только `MyProfileStateStore`. Публично экспортированы внутренние presentation-типы `MyProfilePresentationModel`, `MyProfileVisualEnvironment` и `MyProfileContrast`, поэтому минимальная factory-owned surface boundary из `IOS-REQ-1`/`IOS-AC-1` не реализована.

## App-shell allowlist

- Command: `rg -n 'URLSession|/api/profile|/api/interviews/history|fetchInterviewCount|ProfileDTO|InterviewHistoryListDTO' iOS/SysDevScen/SysDevScen/ContentView.swift iOS/SysDevScen/SysDevScen/RootView.swift iOS/SysDevScen/SysDevScen/SysDevScenApp.swift`
- Result: `FAIL`
- Observation: `SysDevScenApp.swift` содержит profile API routes и runtime `StubProfileSessionClient`, а `ContentView.swift`/`RootView.swift` содержат feature repository implementations. `ContentView.swift` также владеет копией mutable `profileState`. Это выходит за allowlist `entry-points, lifecycle, root-routing, dependency-wiring, platform-configuration, target-resources` и нарушает `IOS-AC-2`.
