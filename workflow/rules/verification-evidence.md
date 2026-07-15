# Verification evidence

Verification is a fresh read of current contracts and realized code, not a
writer narrative. The read-only `verifier` assigns every active row in
`verification.md` exactly `PASS`, `FAIL` or `UNKNOWN`.

- `PASS` requires a concrete repo-relative evidence path inside the package
  `evidence/` directory and an existing non-empty file.
- any `FAIL` or `UNKNOWN` blocks `verified`.
- expected evidence from propose is not terminal proof.
- focused task evidence proves task completion but does not prove the whole
  package verified.

After all checks, `capture-verification-state.py` hashes every realized declared
task path, `verification.md`, relevant shared/platform contracts, platform rule
files and every current package evidence file except the state JSON itself.
It writes `evidence/verification-state.json`. `meta.verification_state` points
to that file, `verification_status` becomes `PASS`, and `verified_at` records an
explicit timestamp only after the validator accepts the package.

Any later code, task, design, shared contract, adapter or applicable rule change
makes the fingerprint stale and blocks archive until `$verify` is rerun. Row,
evidence content and evidence set changes are therefore stale-sensitive.

For non-PASS results, persist every concrete row, set meta precedence FAIL over
UNKNOWN, keep terminal timestamp/state null, and list exact non-PASS IDs in
`problems`. Every affected done task is reopened to pending/none by Inline
contract mapping, together with the full transitive dependent closure. An
unmapped problem blocks and returns to plan repair.

Once a recovery task is reimplemented successfully, the old run is invalidated:
all rows return to pending, meta problems/status/timestamp/state return to
empty/pending/null, and historical evidence remains untouched. A scope baseline
captured while meta is FAIL/UNKNOWN authorizes only this exact
`verification.md` reset; initial implementation does not.
