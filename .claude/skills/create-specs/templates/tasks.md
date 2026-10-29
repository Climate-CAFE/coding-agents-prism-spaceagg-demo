# Tasks: <feature title>

> Template for `specs/NN-<feature>/tasks.md`. Replace every `<placeholder>`.
>
> **Checkbox rule:** mark `- [x]` only when the task's definition of done has been verified by running the stated check. Record the verification result in the task's notes. Leave `- [ ]` otherwise.

- **Specification:** `specs/NN-<feature>/spec.md` (approved <YYYY-MM-DD>)
- **Plan:** `specs/NN-<feature>/plan.md` (approved <YYYY-MM-DD>)

## Phase 1: <phase name, e.g. "Data preparation">

- [ ] **T01: <task title>**
  - **Depends on:** none
  - **Serves:** D1, AC1
  - **Description:** <what to do>
  - **Definition of done:** <a checkable condition, e.g. "`<command>` exits 0 and `<output path>` contains <expected property>">
  - **Verification:** <command or inspection performed>
  - **Notes:** <results, links to evidence, or failure details>

- [ ] **T02: <task title>**
  - **Depends on:** T01
  - **Serves:** D2
  - **Description:** <what to do>
  - **Definition of done:** <checkable condition>
  - **Verification:** <command or inspection>
  - **Notes:**

## Phase 2: <phase name, e.g. "Core implementation">

- [ ] **T03: <task title>**
  - **Depends on:** T02
  - **Serves:** D1, D2, AC1
  - **Description:** <what to do>
  - **Definition of done:** <checkable condition>
  - **Verification:** <command or inspection>
  - **Notes:**

## Phase 3: <phase name, e.g. "Validation">

- [ ] **T04: <task title>**
  - **Depends on:** T03
  - **Serves:** AC1, AC2
  - **Description:** <what to do>
  - **Definition of done:** <checkable condition, e.g. "validation report at `<path>` shows AC1 and AC2 pass">
  - **Verification:** <command or inspection>
  - **Notes:**

## Coverage check

Before the work is marked complete, confirm every decision and acceptance criterion appears in at least one task.

| Spec item | Task ID(s) | Covered |
|-----------|------------|---------|
| D1 | T01, T03 | yes / no |
| D2 | T02, T03 | yes / no |
| AC1 | T03, T04 | yes / no |
| AC2 | T04 | yes / no |
