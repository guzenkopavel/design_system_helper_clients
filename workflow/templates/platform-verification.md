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
Каждая атомарная AC/verification dimension получает отдельную row и отдельное
наблюдаемое evidence; одна row не агрегирует независимые dimensions.

## Revalidated engineering scopes and exact verify rules
## Derived method matrix
## Build and integration
## Platform runtime evidence
## Accessibility and design-system
## Native UX verification

Для product-backed `ui` проверить native appearance scenarios из
`platform-ux.md`, включая раздельные light/dark, increased contrast, assistive
semantics, text scaling, motion, device
adaptation и availability fallback с конкретным evidence.

## Native obligation coverage

| Obligation ID | Observation record | Status |
|---|---|---|
| NATIVE-APPEARANCE | pending | pending |
| NATIVE-LIGHT | pending | pending |
| NATIVE-DARK | pending | pending |
| NATIVE-INCREASED-CONTRAST | pending | pending |
| NATIVE-ASSISTIVE-SEMANTICS | pending | pending |
| NATIVE-TEXT-SCALING | pending | pending |
| NATIVE-MOTION | pending | pending |
| NATIVE-DEVICE-ADAPTATION | pending | pending |
| NATIVE-AVAILABILITY-FALLBACK | pending | pending |

Для current v1 product-backed `ui` exact set обязателен. Registry-anchored v0
не получает эту секцию. Verify заменяет `pending` на
package-relative JSON observation record с exact `obligation_id`, собственным
status, русским observation и underlying `evidence_refs`. Row status обязан
совпасть с record; `PASS`/`FAIL` требуют concrete non-empty underlying evidence.
Underlying refs не могут указывать на этот или другой native observation record;
они ссылаются только на raw/non-observation proof.
Exact record schema: [`native-verification-observation.json`](native-verification-observation.json).

## Unverified risks
