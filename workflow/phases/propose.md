---
phase: propose
writes_artifacts:
  - <platform>/specs/<feature>/changes/<change-id>/meta.json
  - <platform>/specs/<feature>/changes/<change-id>/proposal.md
  - <platform>/specs/<feature>/changes/<change-id>/implementation-spec.md
  - <platform>/specs/<feature>/changes/<change-id>/design.md
  - <platform>/specs/<feature>/changes/<change-id>/verification.md
requires_verification: focused
recommended_roles:
  - repo-navigator
  - specification-writer
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
   Select one or more adapter-defined `engineering_scopes` from evidence. Run
   `find-platform-context.py --phase propose` with each selected `--scope` and
   load the exact returned proposal profile plus scope rules.
2. Sequentially dispatch `repo-navigator`, `specification-writer`, optional
   `architecture-designer`, then the adapter boundary guard. Never run writers
   concurrently.
3. Write only the five package artifacts under
   `<package_root>/<feature>/changes/<change-id>/`.
4. Reference shared IDs without copying their observable text. Use adapter
   prefix for platform REQ/AC and trace every ID in verification.
5. Record sorted unique scopes and the exact derived union of adapter-supported
   phase bases plus those scopes in `applicable_rule_files`. Proposal records
   selection evidence, considered exclusions and the exact list; design maps
   applicable rules to decisions or explicit N/A.
6. Candidate meta is `specified`, `tasks_total: 0`, `tasks_done: 0`,
   `verification_status: pending`; validate with `--mode propose --change`.
7. On failure restore `draft` and report blockers.

Apply wording clarity, common system-design and only the resolver-selected
platform corpus. Do not load the flat adapter catalog globally.
Do not create a plan, production code or commit.
