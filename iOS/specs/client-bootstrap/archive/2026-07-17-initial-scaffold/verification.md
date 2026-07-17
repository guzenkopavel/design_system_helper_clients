# Verification — client bootstrap / iOS / initial scaffold

| Contract ID | Layer | Method | Evidence path | Status |
|---|---|---|---|---|
| IOS-REQ-1 | integration | Xcode project and target discovery | expected evidence before terminal verification | pending |
| IOS-AC-1 | build | simulator application build | expected evidence before terminal verification | pending |

## Revalidated engineering scopes and exact verify rules

Application, UI, and Xcode scopes remain sealed; terminal verification is pending because simulator test launch was interrupted by the local service.

## Derived method matrix

Project discovery and a simulator build cover integration while test execution remains a separate unresolved environment check.

## Build and integration

The discovered application scheme builds successfully for the available simulator runtime.

## Platform runtime evidence

Test bundles compiled, but simulator launch ended with a local Mach service error before test completion.

## Accessibility and design-system

Template resources are present, but accessibility and design-system acceptance remain future product work.

## Unverified risks

Unit and UI test execution, runtime behavior, and product-level semantics remain unverified.
