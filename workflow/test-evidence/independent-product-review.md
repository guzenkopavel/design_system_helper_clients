# Independent product specification review evidence

## Scope and documentation impact

- scope: `common`; one product contract for iOS and Android;
- `README.md`: manual `no-impact` — no new top-level capability/entrypoint;
  generated structural projections may refresh mechanically;
- `workflow.md`: `update` — practical six-context loop, receipt and fallback;
- `deep-info.md`: `update` — role/script/fingerprint/receipt/downstream wiring.

## RED baseline

Before this change Elaborate recorded a self-authored lens table inside
`spec.md`. There was no independent role, subject fingerprint, exact verdict
schema, durable receipt or downstream freshness gate. READY/APPROVED alone was
accepted by platform intake and completed product archive.

RED pressure established missing protection for self-authored PASS, one context
covering all lenses, mixed/stale fingerprints, package add/delete/edit, missing
or duplicate lens, invalid N/A, PASS+blocker, UNKNOWN/same-context fallback,
duplicate run/context/provenance, mixed parent session, single-client review,
reviewer mutation, approval-after-review, PASS without rationale/evidence,
ambiguous metadata, duplicate REQ/AC, READY without receipt, REQ↔AC gap and
symlink/traversal.

## GREEN contract

- one read-only `product-spec-reviewer` invocation per lens in a fresh context;
- exact six lenses and lens-specific semantic checklists;
- snapshot covers all package regular files recursively, excluding only receipt
  and normalizing only one exact Status metadata line;
- approval metadata and every normative/unknown file remain fingerprinted;
- exact verdict/finding schema with runtime/parent/context/provenance
  attestation, unique invocation identities and both clients checked;
- validator checks attestation/schema/freshness but does not claim to prove
  runtime isolation; coordinator-created contexts and retained runtime-issued
  invocation evidence establish/audit actual independence;
- same-context fallback is `UNKNOWN`, never independent PASS;
- coordinator-only deterministic `review-verdicts.json` aggregate with
  `PASS|GAPS|UNKNOWN`; exact non-green findings remain durable;
- final check enforces PASS/current fingerprint, exact metadata, approval,
  READY, unique REQ/AC coverage and UX artifact/readiness link;
- product-backed platform intake and completed product archive reuse the gate.

## Pressure results

| Scenario | Expected |
|---|---|
| self-authored PASS / wrong role | reject |
| one context for all lenses | reject duplicate context |
| mixed/stale fingerprint or approval after review | DRAFT / reject |
| package edit/add/delete/unknown file | fingerprint changes |
| missing/duplicate lens or run | reject |
| product/cross-client N/A | reject |
| optional N/A without package rationale/ref | reject |
| PASS without substantive rationale/evidence refs | reject |
| PASS with blocker | reject |
| GAP/UNKNOWN without evidence | reject |
| same-context parent == reviewer context | only UNKNOWN; durable UNKNOWN receipt, readiness blocked |
| external/manual without explicit invocation evidence | only UNKNOWN; readiness blocked |
| mixed parent session / duplicate provenance | reject; no receipt |
| exact valid GAP/UNKNOWN set | durable GAPS/UNKNOWN receipt; CLI nonzero; readiness blocked |
| only iOS checked | reject |
| platform implementation detail in product contract | semantic GAP |
| READY/APPROVED without fresh receipt | downstream blocked |
| REQ↔AC gap after fresh receipt | final check blocked |
| duplicate/conflicting critical metadata | final check blocked |
| duplicate REQ or AC identity | final check blocked before mapping collapse |
| child/root symlink, unsafe feature | fail closed |
| duplicate exact Status metadata | fail closed |
| DRAFT→READY exact Status change after receipt | fingerprint remains current |

## Focused commands

```text
python3 workflow/scripts/validate-product-spec.py --self-test
validate-product-spec self-test: PASS (fingerprint, isolated lenses, receipt, readiness, pressure)

python3 workflow/scripts/validate-platform-change.py --self-test
validate-platform-change self-test: PASS (change-aware lifecycle and adversarial gates)

python3 workflow/scripts/archive-change.py --self-test
archive-change self-test: PASS (implementation/product gates, isolation, collision safety)

python3 workflow/scripts/harness-lint.py --self-test
harness-lint self-test: PASS (profiles + hooks + deep review security mutations)
harness-docs self-test: PASS (markers, freshness, parity, isolation)

python3 workflow/scripts/harness-docs.py render
python3 workflow/scripts/harness-docs.py check --json
second render changed no files; check: PASS

python3 workflow/scripts/harness-lint.py
Harness lint: grade A (0 critical, 0 warnings)

python3 -m py_compile workflow/scripts/validate-product-spec.py \
  workflow/scripts/validate-platform-change.py \
  workflow/scripts/archive-change.py workflow/scripts/harness-lint.py
PASS

git diff --check
PASS
```

Repository-level security checks and independent active-package platform checks
remain part of the final harness-change regression run.
