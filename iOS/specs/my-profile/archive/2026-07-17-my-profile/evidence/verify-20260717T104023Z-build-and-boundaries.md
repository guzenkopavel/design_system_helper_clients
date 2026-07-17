# Fresh verify: build and boundaries

## Consumer build

- Command: `bash workflow/scripts/test-watchdog.sh --max-seconds 300 --stall-seconds 60 --max-output-lines 40000 -- xcodebuild -project iOS/SysDevScen/SysDevScen.xcodeproj -scheme SysDevScen -destination 'platform=iOS Simulator,name=iPhone 17' build`
- Destination: iPhone 17, iOS 26.5 simulator
- Exit status: `0`
- Duration: `16.25s`
- Result: `PASS`
- Observation: `BUILD SUCCEEDED`; graph содержит
  `SysDevScen -> MyProfileFeature -> AuthFeature`.

## Physical package graph

- Command: `swift package --package-path iOS/MyProfileFeature describe --type json`
- Command: `swift package --package-path iOS/MyProfileFeature show-dependencies --format json`
- Result: `PASS`
- Observation: package публикует один library product `MyProfileFeature`,
  содержит отдельные library/test targets и зависит только от `AuthFeature`.

## Public API and visibility

- Result: `PASS`
- Observation: production source публикует только
  `MyProfileFeatureFactory`, его `init` и `makeProfileView`.
  `MyProfileView`, `MyProfileStateStore`, repository, domain state,
  presentation model и visual environment остаются internal. Consumer вызывает
  `MyProfileFeatureFactory().makeProfileView`.

## App-shell allowlist

- Result: `FAIL`
- Observation: `ContentView` и `RootView` принимают только `AnyView` и не
  владеют mutable feature state. Но `SysDevScenApp.swift` всё ещё содержит
  production type `StubProfileSessionClient`, profile/history/logout request
  matching, fixture payloads и сценарную feature-логику. Это выходит за
  `entry-points, lifecycle, root-routing, dependency-wiring,
  platform-configuration, target-resources`.
