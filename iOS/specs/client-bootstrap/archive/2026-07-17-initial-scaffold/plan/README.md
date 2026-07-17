# Plan — client bootstrap / iOS / initial scaffold

## Planning frame

One bounded task records and builds the already generated iOS project shell without adding product behavior.

## Revalidated engineering scopes and exact rules

The sealed selection covers application, UI, and Xcode risks represented by the generated project and targets.

## Assumptions

The generated scaffold is temporary infrastructure and may be replaced by later product-backed changes.

## DAG

`task-001` has no dependencies and is the only bootstrap task.

## Tasks

`task-001` captures the generated project and its focused Xcode evidence.

## Estimates and multipliers

The bounded import and verification fit within a half-day to one-day integration range.

## Verification strategy

Discover the scheme and simulator destination, build the application, and record simulator test limitations separately.

## Test and performance budgets

Build and test checks use watchdog limits and make no product performance claim.

## Checkpoints

Commit only after staged task evidence and the repository pre-commit gate pass.

## Risks

Future features must not treat template UI or persistence behavior as an approved product contract.
