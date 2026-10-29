# create-specs: gate checklists and change control

The phase order and rules are in `SKILL.md`. This file holds only the checks for each gate and the procedure for changes after approval.

## Gate 1: specification approved (`spec.md`)

Before asking for review, confirm that `spec.md` has:

- A scientific goal stated as a question or hypothesis, with scope and out-of-scope items.
- Inputs and provenance for every dataset (source, version or date, limitations).
- A decision (D#) for every methodological choice, each with a rationale. Choices not yet made are `PENDING` and listed under open questions.
- An acceptance criterion (AC#) for each requirement, phrased so a script or an explicit inspection gives pass or fail.

Record the approver and date, then set status to `approved`.

Common mistakes:
- Vague criteria such as "the method works well." Replace them with a measurable statement and the threshold the human has set.
- Decisions with no rationale. Even "requested by the project lead" is a valid rationale.

## Gate 2: plan approved (`plan.md`)

Before asking for review, confirm that `plan.md`:

- References the approved spec by version or commit.
- Maps every D# and AC# to at least one plan element and one validation step.
- Lists every parameter that affects results, its value, and where it is set.
- Contains no task list or checkboxes.

If the plan reveals a gap in the spec, return to the spec, amend it, and get re-approval for the changed items.

## Tasks and status

- `tasks.md`: each task has an ID, dependencies, the D#/AC# it serves, and a checkable definition of done. Tasks should not start before both gates are approved.
- `status.md`: update at the end of every session, and whenever a task completes, a blocker appears, a deviation is proposed, or approval is needed.

## Handling change after approval

Changes are never silent edits:

1. Record the proposed change and its reason in `status.md` under deviations or decisions requiring approval.
2. Amend the affected spec or plan section and mark it `amended, awaiting approval`.
3. Obtain re-approval at the relevant gate.
4. Update the traceability links and the tasks that depend on the change.
