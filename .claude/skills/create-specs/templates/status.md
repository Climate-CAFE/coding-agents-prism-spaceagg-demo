# Status: <feature title>

> Template for `specs/NN-<feature>/status.md`. Update at the end of every working session and whenever a blocker, deviation, or approval request arises. Replace every `<placeholder>`.

- **Last updated:** <YYYY-MM-DD>
- **Current phase:** <explore | draft specification | awaiting approval (spec) | plan | awaiting approval (plan) | tasks | implementation and validation | complete>
- **Completed on:** <YYYY-MM-DD, or "not complete">

## Approval state

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | <draft / awaiting approval / approved> | <name or "pending"> | <date or "pending"> |
| plan.md | <draft / awaiting approval / approved> | <name or "pending"> | <date or "pending"> |

## Completed tasks

- <T0#: task title> (verified in tasks.md). Verified by: <command or inspection>. Evidence: <path>.

## Work in progress

- <T0#: task title>. Current state: <what is happening>.

## Blockers

| ID | Blocker | Affects | Owner | Since |
|----|---------|---------|-------|-------|
| B1 | <description> | <task or decision IDs> | <owner> | <YYYY-MM-DD> |

## Decisions requiring human approval

| ID | Decision or change requested | Reason | Needed before |
|----|------------------------------|--------|---------------|
| D# | <decision or change> | <reason> | <task or phase> |

## Data status

| Dataset | Status | Version or checksum | Notes |
|---------|--------|---------------------|-------|
| <dataset> | <available / pending access / partial / invalid> | <version> | <notes> |

## Deviations

Record any departure from an approved decision or plan element. Do not proceed down a deviating path until it is approved.

| ID | Deviation | Reason | Approval status |
|----|-----------|--------|-----------------|
| X1 | <what differs from the approved spec or plan> | <why> | <pending / approved by <name> on <date>> |

## Validation results

| ID | Status | Latest evidence | Checked on |
|----|--------|-----------------|------------|
| AC1 | <not started / in progress / passing / failing> | <path or result> | <YYYY-MM-DD> |
| AC2 | <not started / in progress / passing / failing> | <path or result> | <YYYY-MM-DD> |

## Next steps

1. <next action, with the task ID or approval it depends on>
2. <next action>
