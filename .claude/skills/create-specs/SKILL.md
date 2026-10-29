---
name: create-specs
description: Specification-driven workflow with human approval gates for new analysis features. Use when starting a feature, or when asked to write a spec, plan, task list, or status file. Provides templates for spec.md, plan.md, tasks.md, and status.md.
license: Proprietary
metadata:
  version: "1.0"
  category: research-workflow
---

# create-specs

A reusable workflow for turning an open-ended research question into an approved specification, a plan, a task list, and a tracked status. It is project-agnostic: every scientific decision is a placeholder until a human approves it.

## When to use

- Starting a new research project, analysis, or experiment.
- The user asks for a spec, plan, task list, or status update for research work.
- Resuming a project where the specification files are missing or stale.

Do not use this Skill for small, self-contained code edits that have no scientific decisions attached.

## Workflow

Follow the phases in order. Do not skip a phase, and do not start the next phase until its gate is satisfied. [references/workflow.md](references/workflow.md) lists the gate checklists and the procedure for changes after approval.

1. **Explore.** Read the available inputs (data descriptions, prior notes, literature the user points to). Record open questions. Do not make methodological choices yet.
2. **Draft specification.** Create `specs/NN-<feature>/spec.md` from [templates/spec.md](templates/spec.md). Every methodological choice gets an ID (D1, D2, …) with rationale. Every requirement gets a testable acceptance criterion (AC1, AC2, …). Unresolved choices go under open questions, not into the decisions table as guesses.
3. **Human approval (gate 1).** Stop and ask the human to review and approve `spec.md`. Set its approval status to `approved` only after an explicit human sign-off. Do not infer approval from silence or from the user asking for the next step on a different topic.
4. **Plan.** Create `specs/NN-<feature>/plan.md` from [templates/plan.md](templates/plan.md). It must reference the approved specification and trace every decision and acceptance criterion to an implementation element.
5. **Human approval (gate 2).** Ask for review of `plan.md`. Record approval the same way as gate 1.
6. **Tasks.** Create `specs/NN-<feature>/tasks.md` from [templates/tasks.md](templates/tasks.md). Each task has an ID (T01, T02, …), dependencies, references to decisions or acceptance criteria, and a definition of done.
7. **Implementation and validation.** Work through tasks in dependency order. Check a box (`- [x]`) only when the task's definition of done has been verified by running the check, not when the code merely looks finished.
8. **Update status.** Keep `specs/NN-<feature>/status.md` (from [templates/status.md](templates/status.md)) current at the end of each working session and whenever a blocker, deviation, or approval request arises.

## Output location

Write the artifacts to `specs/NN-<feature>/` in the project root, one folder per feature.

- **Number:** use the next available two-digit number (`01`, `02`, …). Scan existing `specs/` folders, take the highest number, and add one. Never renumber or rename existing features.
- **Name:** a short kebab-case feature name supplied by the user (for example `specs/02-churn-cohort-split/`).

```
specs/NN-<feature>/
├── spec.md     # requirements, decisions (D#), acceptance criteria (AC#)
├── plan.md     # implementation design
├── tasks.md    # checkboxes (T##)
└── status.md   # progress, completion date, validation results
```

## Rules

- **Placeholders, not decisions.** The templates contain placeholders such as `<dataset name>` or `<primary metric>`. Replace them with project-specific content only after the human has supplied or approved it. Never fill in a scientific choice (model family, threshold, split strategy, significance level, and so on) on the user's behalf without marking it as a proposal awaiting approval.
- **Traceability.** Every decision (D#) and acceptance criterion (AC#) must be referenced by at least one plan element and at least one task before the work is considered complete. Flag any orphan in `status.md`.
- **Approval is explicit.** Record who approved, and when, in the approval-status block. Until then, the status is `draft` or `awaiting approval`.
- **Checkboxes are evidence.** `- [x]` means the definition of done was verified. Record how it was verified in the task's notes.
- **Checkboxes live only in `tasks.md`.** `plan.md` describes the approach and must not repeat task status. `status.md` names completed tasks in plain text, without checkboxes. Open questions in `spec.md` are the only other checkboxes.
- **Deviations are recorded, not hidden.** If implementation departs from an approved decision, add an entry to the deviations section of `status.md` and request approval before continuing down that path.
- **Stop at gates.** At each human approval gate, end the turn with a clear request for review. Do not proceed into the next phase on your own.
- **Keep templates intact.** When creating project files, copy the template structure and section headings. Do not delete sections; mark unused ones as `N/A` with a reason.

## Reusing this Skill

To adapt the Skill to a new domain, edit only the templates' placeholder text and the gate checklists in `references/workflow.md`. Do not add domain-specific defaults, thresholds, or methods to this file.
