# Verification — <feature> / <platform> / <change-id>

<!-- Описание методов, наблюдений, рисков и результатов писать по-русски;
точные statuses, contract IDs, paths, commands и schema labels не переводить. -->

## Modularity verification

- Dependency graph: pending
- Public API and visibility: pending
- Module-level tests: pending
- Consumer integration and build: pending
- App-shell allowlist: pending

| Contract ID | Layer | Method | Evidence path | Status |
|---|---|---|---|---|
| REQ-1 | contract | requirement review | expected evidence before verify | pending |
| AC-1 | UI | platform runtime scenario | expected evidence before verify | pending |
| <PLATFORM_PREFIX>-REQ-1 | design | design review | expected evidence before verify | pending |
| <PLATFORM_PREFIX>-AC-1 | unit | test name | expected evidence before verify | pending |

`verify` заменяет ожидаемые описания конкретными package-relative путями
`evidence/...` и точными статусами `PASS`, `FAIL` или `UNKNOWN`.

## Revalidated engineering scopes and exact verify rules
## Derived method matrix
## Build and integration
## Platform runtime evidence
## Accessibility and design-system
## Native UX verification

Для product-backed `ui` проверить native appearance scenarios из
`platform-ux.md`, включая light/dark/contrast, accessibility/motion, device
adaptation и availability fallback с конкретным evidence.

## Unverified risks
