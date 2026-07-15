# iOS addendum: Implement

Load the adapter and applicable iOS rule files before production writes. The
implementation writer may mutate only task-declared paths under the iOS
production root, excluding `iOS/specs` and `iOS/workflow`; package task/evidence
state is limited to selected task/meta and its canonical task evidence/baseline
files.

In recovery only, after focused task evidence passes, use the recovery baseline
permission to reset package `verification.md` rows to pending and clear terminal
meta. Preserve old iOS verification evidence as audit history; dependent tasks
reopened by Verify continue in DAG order.

Use behavior-first tests, architecture boundaries, structured concurrency and
discovered Xcode configuration. UI work includes simulator behavior,
accessibility identifiers/semantics, design-system tokens and localization.
Never broaden the task to unrelated iOS cleanup.
