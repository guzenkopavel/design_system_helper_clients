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
- каждый атомарный AC/`Verification dimension` имеет ровно одну verification
  row и собственное concrete observation; adjacent PASS и prose не заменяют
  отсутствующую evidence;
- ненаблюдённая required runtime, appearance или accessibility dimension имеет
  статус `UNKNOWN`, даже если соседний outcome прошёл.

Для каждого current v1 product-backed `ui` package common exact set:
`NATIVE-APPEARANCE`, `NATIVE-LIGHT`, `NATIVE-DARK`,
`NATIVE-INCREASED-CONTRAST`, `NATIVE-ASSISTIVE-SEMANTICS`,
`NATIVE-TEXT-SCALING`, `NATIVE-MOTION`, `NATIVE-DEVICE-ADAPTATION`,
`NATIVE-AVAILABILITY-FALLBACK`. Каждая row ссылается на отдельный exact JSON
observation record (`schema_version`, `obligation_id`, `status`, `observation`,
`evidence_refs`). Row/record status обязаны совпадать; PASS/FAIL record имеет
concrete non-empty underlying refs внутри package evidence и не может ссылаться
ни на себя, ни на любой другой native observation record. Underlying refs —
только raw/non-observation evidence artifacts, поэтому cross-record и циклическое
обоснование PASS запрещены. UNKNOWN record не превращается в PASS через prose.
Schema задан в
[`native-verification-observation.json`](../templates/native-verification-observation.json).

Non-PASS native ID входит в `meta.problems` и переоткрывает все `ui` tasks с их
dependent closure. Если `ui` task отсутствует, recovery fail-closed возвращает
plan repair; native ID не подменяется REQ/AC.
Registry-anchored v0 завершает только historical verification rows/checks:
`NATIVE-*` rows/records к нему не добавляются даже при UI scope.

Verify is bounded by `evidence/verify-scope-baseline.json`. Pre-verifier snapshot
and immediate post-verifier check require zero production/task/plan/contract/
adapter/rule changes and preserve pre-existing dirty work. Only new verifier
evidence, `verification.md`, verification meta fields and state file are allowed;
existing task/historical evidence is immutable. Recovery task reopening is a
coordinator step after this check.

After all checks, `capture-verification-state.py` hashes every realized declared
task path, `verification.md`, relevant shared/platform contracts, exact
`applicable_rule_files` and every current package evidence file except the state
JSON itself. It also hashes a deterministic semantic adapter projection:
identity/ownership boundaries, contract prefix/guard/checks, all phase base
profiles and only the selected scope mappings. The raw adapter and flat catalog
are not fingerprint inputs.

For every adapter with the `verify` capability, relevant terminal contracts are
a platform-neutral mandatory set: this rule, `workflow/phases/verify.md`, and
`<platform>/workflow/phases/verify.md`. State capture loads and fingerprints
them directly, outside the sealed engineering union in
`applicable_rule_files` and `plan/rule-selection.json`. A path already selected
by that union is deduplicated. A missing mandatory terminal contract blocks
capture instead of producing a partial fingerprint.
It writes `evidence/verification-state.json`. `meta.verification_state` points
to that file, `verification_status` becomes `PASS`, and `verified_at` records an
explicit timestamp only after the validator accepts the package.

Any later code, task, design, shared contract, selected semantic profile or
applicable rule change makes the fingerprint stale and blocks archive until
`$verify` is rerun. An unrelated unselected rule/profile change does not stale
the package. Row, evidence content and evidence set changes remain
stale-sensitive.

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
