# Implementation Plan: <feature title>

> Template for `specs/NN-<feature>/plan.md`. Replace every `<placeholder>`. Do not begin this plan until the referenced specification is approved.
>
> **Tracking rule:** do not add task lists or checkboxes here. Task status lives only in `tasks.md`.

## Reference to approved specification

- **Specification:** `specs/NN-<feature>/spec.md`
- **Specification version or commit:** <version or commit>
- **Specification approved by:** <name or role> on <YYYY-MM-DD>
- **Plan status:** `draft` <!-- draft | awaiting approval | approved -->

## Technical approach

<Describe the overall approach in a paragraph or two. Explain how it realizes the decisions D1 onward and why it was chosen over the alternatives listed below.>

## Modules and data flow

<Name each module or stage and what it consumes and produces. A simple diagram or ordered list is sufficient.>

1. **<stage name>**: input <input> → output <output>. Implemented in `<path>`.
2. **<stage name>**: input <input> → output <output>. Implemented in `<path>`.

## Skills applied

<List each reusable Skill this plan uses and what it supplies (for example, a script or a method). Write "None" if no Skill applies. Do not restate the Skill's guidance here.>

- **<skill name>:** <what it supplies, and where it is used in this plan>.

## Configuration

Every parameter that affects results is listed here with its value and where it is set.

| Parameter | Value | Set in | Governed by decision |
|-----------|-------|--------|----------------------|
| <parameter> | <value or "to be set"> | <config file or flag> | D1 |
| Random seed | <seed> | <location> | <decision or "reproducibility constraint"> |

## Data manifest

| Dataset | Version or date | Location or checksum | Transformations applied | Stage that uses it |
|---------|-----------------|----------------------|-------------------------|--------------------|
| <dataset> | <version> | <path or checksum> | <transformations> | <stage> |

## Traceability

Every decision and acceptance criterion from the specification must appear here and point to at least one plan element and one task.

| Spec item | Plan element(s) | Task ID(s) | Evidence location |
|-----------|-----------------|------------|-------------------|
| D1 | <module or stage> | T01, T02 | <path to output> |
| D2 | <module or stage> | T03 | <path to output> |
| AC1 | <module or stage that produces the measured result> | T04 | <path to validation report> |
| AC2 | <module or stage> | T05 | <path to validation report> |

## Validation strategy

<Describe how each acceptance criterion will be verified, in order.>

- **AC1:** <command, script, or analysis that produces the evidence>. Pass condition: <condition>.
- **AC2:** <command, script, or analysis>. Pass condition: <condition>.
- **Unit and integration checks:** <what is tested and how to run it>.
- **Reproducibility check:** <how a clean re-run will be confirmed to match results>.

## Risks

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| <risk, e.g. "<data limitation>"> | <low/medium/high> | <low/medium/high> | <mitigation> | <owner> |

## Alternatives considered

| Alternative | Why it was not chosen |
|-------------|-----------------------|
| <alternative approach> | <reason> |
