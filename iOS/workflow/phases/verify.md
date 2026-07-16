# iOS addendum: Verify

Resolve the exact verify profile with unchanged scopes. Rerun applicable unit, UI, simulator, accessibility, design-system,
localization, concurrency and Xcode build checks against current code. Do not
invent scheme, target or destination names; discover them from the repository.
The verifier writes only package evidence and returns exact PASS/FAIL/UNKNOWN.
Derive commands from project/package configuration, use planned watchdog budgets
for nontrivial runs, and compare performance only against a recorded compatible
baseline.
For product-backed UI, verify native appearance scenarios from `platform-ux.md`;
unavailable SDK/runtime remains UNKNOWN and is never an invented rendering PASS.

For v1, verify realized package/target dependency graph, public API/visibility,
unit-level tests, consumer integration/build and app-target allowlist. Missing
project/package tooling or consumer destination is `UNKNOWN`, not PASS.
For registry-anchored v0, run only historical selected checks including adapter
`legacy_task_checks`; do not add v1 app-target/composition assertions or expand
ownership.
