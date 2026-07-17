# Reconciliation evidence — task-001

## Intended paths

- iOS/AuthFeature/Package.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/AuthConfiguration.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/AuthError.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/AuthAPIClient.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/SessionSecretStore.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/Contracts/TimeProvider.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/SessionState.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/CheckEmailUseCase.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/CheckSessionUseCase.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/LogInUseCase.swift
- iOS/AuthFeature/Sources/AuthFeature/Domain/UseCases/RegisterAccountUseCase.swift
- iOS/AuthFeature/Tests/AuthFeatureTests/Domain/AuthConfigurationTests.swift
- iOS/AuthFeature/Tests/AuthFeatureTests/Domain/AuthErrorTests.swift

## Focused checks

swift build --package-path iOS/AuthFeature → Build complete! (0.21s)

- Result: PASS
