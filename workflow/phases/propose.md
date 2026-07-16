---
phase: propose
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
  - <platform>/specs/<feature>/changes/<change-id>/proposal.md
  - <platform>/specs/<feature>/changes/<change-id>/implementation-spec.md
  - <platform>/specs/<feature>/changes/<change-id>/design.md
  - <platform>/specs/<feature>/changes/<change-id>/verification.md
  - <platform>/specs/<feature>/changes/<change-id>/platform-ux.md (product-backed ui only)
requires_verification: focused
recommended_roles:
  - repo-navigator
  - specification-writer
  - adapter-selected platform UX designer (product-backed ui only)
  - architecture-designer
---

# Phase: Propose

Create one platform implementation package without production code.

Form: `propose <platform> <feature> [--change <change-id>] [--tier quick|standard|extended] [--technical-only]`.
Platform and feature are required. Feature/change are strict kebab-case. An
omitted change defaults to the feature slug for a new cycle. Existing package,
archive or tombstone identity collisions block before writes. Missing, unknown
or unavailable adapter also blocks before writes.

Product-backed intake requires the exact active shared spec at
`specs/product/<feature>/spec.md`, `READY`, explicit `APPROVED` and evidence.
Technical-only intake requires `Product impact assessment: NONE` and evidence.

Workflow:

1. Discover real context and separate existing paths from greenfield proposals.
   Read `<platform>/specs/<feature>/SPECIFICATION.md` when present as immutable
   current platform baseline; for product-backed intake also distinguish the
   active shared candidate from `specs/product/<feature>/SPECIFICATION.md`.
   Select one or more adapter-defined `engineering_scopes` from evidence. Run
   `find-platform-context.py --phase propose` with each selected `--scope` and
   load the exact returned proposal profile plus scope rules.
2. Sequentially dispatch `repo-navigator`, `specification-writer`, then for
   product-backed `ui` the adapter-selected platform UX designer, then
   `architecture-designer`, then the adapter boundary guard. Never run writers
   concurrently. The UX owner writes only `platform-ux.md`; architecture reads
   and incorporates its decisions.
3. Write the five base artifacts plus conditional `platform-ux.md` under
   `<package_root>/<feature>/changes/<change-id>/`.
   Authored prose в каждом Markdown artifact писать по-русски по
   [`artifact-language`](../rules/artifact-language.md); exact machine schema,
   IDs, paths и code/API names сохранять без перевода. Проверка выполняется по
   каждому substantive block, поэтому русский padding не скрывает English prose.
4. Reference shared IDs without copying their observable text. Use adapter
   prefix for platform REQ/AC and trace every ID in verification.
   `implementation-spec.md` must be the complete post-change platform contract,
   not a delta: unchanged applicable platform requirements remain represented.
5. Record sorted unique scopes and the exact derived union of adapter-supported
   phase bases plus those scopes in `applicable_rule_files`. Proposal records
   selection evidence, considered exclusions and the exact list; design maps
   applicable rules to decisions or explicit N/A.
6. Candidate meta is `specified`, `tasks_total: 0`, `tasks_done: 0`,
   `verification_status: pending`; validate with `--mode propose --change`.
7. `design_gate` cannot PASS until conditional platform UX is READY with no
   gaps and design/verification trace it. On failure restore `draft` and report blockers.

Apply wording clarity, common system-design and only the resolver-selected
platform corpus. Do not load the flat adapter catalog globally.
The base profile always applies
`workflow/rules/system-design/modularity.md` plus the adapter platform
modularity rule. `design.md` must contain the exact structured `Modularity
decision`; `isolated` selects the adapter isolation scope, while deviation/N/A
must satisfy their evidence contracts. Dispatch the platform boundary guard
after architecture and return its structured verdict to the architecture owner.
Missing/`BLOCK` verdict prevents `design_gate: PASS`.
New meta and rule-selection candidates use `modularity_contract_version: 1`.
Capability triggers, app-shell allowlist/ownership and existing repo-relative
evidence paths use the exact machine schema from the modularity rule; deviation
is never allowed in an application target/module.
Do not create a plan, production code or commit.
