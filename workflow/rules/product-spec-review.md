# Independent product specification review

`$elaborate` owns the internal gate. There is no separate user-facing skill.
The review subject is one exact active `specs/product/<feature>/` package and the
six canonical lenses are, in order:

1. `product`;
2. `ux-accessibility`;
3. `design-system`;
4. `data-analytics-privacy`;
5. `security`;
6. `cross-client-parity`.

Product and cross-client parity are always `REQUIRED`. An optional lens may be
`NOT_APPLICABLE` only with substantive rationale derived from named files in
the fingerprinted package. Each lens is invoked exactly once in a separate fresh
`product-spec-reviewer` context. The invocation receives only the exact
package, requested lens and common subject fingerprint. It receives no writer
rationale or other lens output. One context cannot review multiple lenses.

A runtime without an independent subagent context must record
`independent_context: false`, `verdict: UNKNOWN`; the package stays `DRAFT`.
Same-context review (`context_id == parent_context_id`) or unavailable
invocation evidence never becomes an independent PASS.

## Lens semantics

- `product`: problem/outcome/scope/non-goals, requirement clarity, observable
  behavior, success signals, alternatives, exact READY coherence и атомарная
  REQ↔AC/evidence dimension;
- `ux-accessibility`: journey/flows/states, content, interaction semantics,
  accessibility and localization outcomes without platform widgets;
- `design-system`: shared component roles, token/semantic intent, consistency
  and justified cross-client variability without implementation selection;
  enforce calm soft-blue semantic roles, quiet neutral surfaces,
  light/dark/high-contrast and non-color cues; reject Liquid Glass/Material APIs
  from the shared product layer;
- `data-analytics-privacy`: data lifecycle/minimization, consent, retention,
  analytics events/properties, measurement integrity and privacy outcomes;
- `security`: trust boundaries, sensitive data, authorization, threats, abuse
  cases, misuse/recovery and fail-safe product behavior;
- `cross-client-parity`: both iOS and Android behavior/states/constraints,
  intentional differences, no hidden fork and testable parity evidence.

## Reviewer boundary

The reviewer is read-only. It never edits/fixes the package, approves product
behavior, assigns READY, creates/aggregates a receipt, reads prior lens results
or reviews platform implementation. Platform SDK/framework/module/architecture
details in the shared product contract are a semantic `GAP`, not platform
review work.

Each invocation emits the exact JSON schema in
[`product-review-verdict.json`](../templates/product-review-verdict.json).
`PASS` and `N/A` require `independent_context: true`; both iOS and Android must
be checked. Every verdict, including PASS, requires substantive package-derived
rationale and non-empty subject `evidence_refs`. Product/cross-client N/A,
PASS with a blocker, GAP/UNKNOWN without findings, duplicate run/context
identity, mixed parent review sessions or a mixed fingerprint is invalid.

The JSON is an exact provenance attestation, not cryptographic proof of runtime
isolation. The validator checks schema, non-placeholder `runtime`, `run_id`,
`parent_context_id`, distinct `context_id`, `provenance_ref`, uniqueness and
freshness. Actual independence is established by the Elaborate coordinator
creating six real fresh read-only runtime contexts and retaining runtime-issued
invocation evidence for audit. All verdicts share one parent coordinator review
session. External/manual review needs explicit invocation evidence; without it
the only valid decision is `UNKNOWN` and the gate stays non-green.

## Durable gate

`workflow/scripts/validate-product-spec.py` is the stdlib authority:

```text
validate-product-spec.py snapshot --feature <feature>
validate-product-spec.py validate-verdict --feature <feature> --verdict <path>
validate-product-spec.py aggregate --feature <feature> --verdict <path>... [--write]
validate-product-spec.py check --feature <feature>
```

`snapshot` fingerprints every recursively discovered regular file in the active
package except feature-root `SPECIFICATION.md`, including unknown files and
human approval metadata. `SPECIFICATION.md` is immutable read-only delivered
baseline for the candidate lifecycle, not candidate input to final lenses. Add/delete/edit
changes the fingerprint. Symlinks and unsafe feature identity fail closed. Only
root `review-verdicts.json` is also excluded. In `spec.md` only the exact Status
metadata line is normalized, so `DRAFT → READY` after a green receipt does not
make that receipt self-stale. No other subject content is normalized/excluded.

`aggregate` accepts exactly six schema-valid unique verdicts at one current
fingerprint, with unique run/context IDs and one parent review session. It may
write the canonical `review-verdicts.json` even when the deterministic status is
`GAPS` or `UNKNOWN`, preserving current findings durably; the CLI returns
non-zero for those non-green states. Only the Elaborate coordinator/writer may
write the receipt; reviewers never do. Missing, duplicate, mixed or invalid
verdicts produce no receipt. `spec.md` contains only static links to that
receipt, not a copied/self-referential verdict table.

`check` requires a current `PASS` receipt, exact lenses, READY, exactly one of
every critical metadata field, explicit APPROVED human metadata, unique REQ/AC
IDs with complete coverage, both clients and coherent UX artifact/readiness
links. Он также требует exact `Readiness Decision: READY/none`, terminal PASS
во всех Client Readiness rows, `None` в Open Questions и уникальную
`Verification dimension` для каждого атомарного AC. GAP, UNKNOWN, ambiguous metadata, a missing/duplicate lens, mixed/stale
fingerprint or missing receipt keeps the package DRAFT and blocks fan-out.

## Ordering

1. Author a `DRAFT` candidate.
2. Run isolated review/fix cycles without treating intermediate outputs as a
   durable receipt.
3. Obtain explicit human approval and record approver/evidence. This changes the
   subject fingerprint.
4. Close blockers and set exact `Readiness Decision: READY/none` while metadata
   Status remains `DRAFT`; snapshot again; run all six final fresh isolated lenses against that exact
   approved fingerprint.
5. Coordinator aggregates the receipt.
6. Change only exact Status metadata from `DRAFT` to `READY`.
7. Run final `check`; stop before platform fan-out on any failure.

Any later package edit except exact Status metadata invalidates the receipt and
requires all six isolated reviews again.
