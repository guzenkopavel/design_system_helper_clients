# iOS addendum: Implement

Load the exact adapter implement profile and stored scope rules before production writes. The
implementation writer may mutate only task-declared paths under the iOS
production root, excluding `iOS/specs` and `iOS/workflow`; package task/evidence
state is limited to selected task/meta and its canonical task evidence/baseline
files.

In recovery only, after focused task evidence passes, use the recovery baseline
permission to reset package `verification.md` rows to pending and clear terminal
meta. Preserve old iOS verification evidence as audit history; dependent tasks
reopened by Verify continue in DAG order.

Use behavior-first tests, architecture boundaries, structured concurrency and
discovered Xcode configuration. Nontrivial checks use the common watchdog with
the planned finite limits. UI work includes simulator behavior,
accessibility identifiers/semantics and design-system tokens. Localization work
is required only for a selected `localization` scope.
Never broaden the task to unrelated iOS cleanup.
Product-backed UI rereads `platform-ux.md` and records Liquid Glass appearance,
contrast, Reduce Transparency/Motion and older-OS fallback evidence.
