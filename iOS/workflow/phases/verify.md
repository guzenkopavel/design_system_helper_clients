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
