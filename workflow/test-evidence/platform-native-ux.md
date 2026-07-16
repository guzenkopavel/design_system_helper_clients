# Platform-native UX harness evidence

## Intake and change plan

- type: common rule/template/validator plus iOS and Android adapter roles/rules;
- operation: add/modify; scope: `cross-platform`;
- failure: product-backed UI could reach design/plan without a native UX
  artifact, availability/fallback decisions or task-level appearance checks;
- invariants: single writer, conditional only for product-backed `ui`, no active
  technical-only migration, no production/UI implementation, no commit.

Root docs dispositions: `README.md` update for the capability/artifact;
`workflow.md` update for operational ordering; `deep-info.md` update plus
generated inventory for schema/state wiring.

## Official-source rationale

- Apple Liquid Glass overview and HIG Materials are canonical references for
  the iOS owner; their JS-only pages are linked, while actual API/OS support
  must be discovered from repository SDK/deployment evidence:
  https://developer.apple.com/documentation/TechnologyOverviews/adopting-liquid-glass
  and https://developer.apple.com/design/human-interface-guidelines/materials.
- Android's official Material 3 Compose guide establishes Material 3 theming;
  M3 Expressive, dependencies and dynamic color remain conditional on current
  repository/product evidence:
  https://developer.android.com/develop/ui/compose/designsystems/material3.

## RED → GREEN → REFACTOR

RED: adapter schema and validator had no `platform_ux`; product-backed UI did
not require `platform-ux.md`, native terms/task checks, design trace or state
fingerprinting. Shared UX did not encode the calm soft-blue semantic default.

GREEN: added common visual-language/template, platform owners and runtime
bindings, exact adapter schema, conditional validation, task checks and terminal
state projection. Propose is sequential: specification → platform UX →
architecture. Technical-only/non-UI remains unchanged.

REFACTOR pressures cover missing artifact; wrong platform/language/color/source;
placeholder/GAPS/open gaps; missing native terms; malformed adapter schema;
missing native task checks; non-UI/technical-only behavior; artifact/adapter
staleness. A shared `visual-language.md` change stales product-backed UI
terminal state but leaves technical-only state unchanged. The common product
layer rejects platform API ownership.

Adversarial follow-up reproduced first-match ambiguity: conflicting duplicate
Color direction/status/source metadata and duplicate Open gaps/substantive
headings previously passed. Validator now requires exactly one of all five
metadata fields and every required heading; missing/duplicate fails closed and
the sole Open gaps must be exact None. `platform-ux.md` presence outside
product-backed `ui` is now an out-of-scope error. Canonical iOS/Android UX roles
must read the common visual-language and own ui-design-system rule completely,
so thin runtime bindings cannot bypass either SSOT.

Final semantic pressure found that substantive UNKNOWN/GAP/GAPS narratives could
coexist with READY/None metadata. A platform-UX-specific marker scan now rejects
`UNKNOWN|GAP|GAPS|PENDING|UNRESOLVED` anywhere without broadening global task/error
placeholder semantics; ordinary wording that an API is unavailable on an older
OS remains valid fallback evidence. Open gaps accepts only normalized sole
`None` (`None.` is valid), not generic or localized open-question synonyms.
The process flow now lists each artifact owner once and marks UX creation and
architecture consumption as conditional.

## Platform evidence

- iOS: Liquid Glass system-first controls/navigation only; content-background
  overuse prohibited; semantic soft-blue tint, light/dark/increased contrast,
  Reduce Transparency/Motion, scrolling legibility, standard components,
  performance and older-OS/SDK fallback are required terms.
- Android: Material 3/MaterialTheme baseline with semantic tonal roles,
  accessible on-colors and light/dark; M3 Expressive requires repository
  SDK/dependency/product evidence; dynamic color is explicit and retains an
  accessible soft-blue fallback with discovered Android 12+ availability.

## Residual risks

This change validates harness contracts and evidence structure only. It does
not render UI, prove SDK/API availability or claim visual correctness; those
remain per-package implementation and native runtime verification evidence.

## Regression results

- `validate-platform-change.py --self-test`: PASS;
- active iOS and Android `client-bootstrap/initial-scaffold` in implement mode:
  VALID independently (technical-only packages were not migrated);
- product/archive/reconcile/pre-commit self-tests: PASS;
- `harness-docs.py render` twice and `check --json`: PASS, second render empty;
- `harness-lint.py`: grade A; lint/docs self-tests: PASS;
- security audit actual/self-test: PASS, complete coverage, zero findings;
- Python compile, `git diff --check` and forbidden-reference scan: PASS.
