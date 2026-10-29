# Specification: <feature title>

> Template for `specs/NN-<feature>/spec.md`. Replace every `<placeholder>`. Delete these instructions when filling in. Do not fill scientific decisions without human approval.

## Approval status

- **Status:** `draft` <!-- draft | awaiting approval | approved | amended, awaiting approval -->
- **Version:** <version or commit>
- **Last changed:** <YYYY-MM-DD>
- **Approved by:** <name or role, or "pending">
- **Approved on:** <YYYY-MM-DD, or "pending">

## Scientific goal

<State the question or hypothesis in one or two sentences. Name the population, phenomenon, or system studied.>

**Motivation:** <why this question matters, and for whom.>

## Scope

**In scope**
- <item>

**Out of scope**
- <item, and why it is excluded>

## Inputs and provenance

| Input | Description | Source and owner | Version or date | Access and license | Known limitations |
|-------|-------------|------------------|-----------------|--------------------|-------------------|
| <input name> | <what it contains> | <source, owner> | <version> | <terms> | <limitations> |

## Methodological decisions

Each decision has an ID, the choice, and the rationale. Mark choices not yet made as `PENDING` and list them under open questions.

| ID | Decision | Rationale | Status |
|----|----------|-----------|--------|
| D1 | <decision, e.g. "<method placeholder>"> | <why this choice> | `PENDING` / `APPROVED` |
| D2 | <decision> | <rationale> | `PENDING` / `APPROVED` |

## Outputs

- <output artifact, e.g. "<table, figure, model, report>">, format <format>, location <path>

## Constraints

- **Compute and time:** <limits>
- **Privacy, ethics, and compliance:** <requirements and approvals>
- **Reproducibility:** <seeds, environment, versioning requirements>
- **Other:** <constraints>

## Acceptance criteria

Each criterion must be testable: a script, a measurement, or an explicit inspection can determine pass or fail. Thresholds marked `<threshold>` must be supplied by the human.

| ID | Criterion | Verification method | Related decisions |
|----|-----------|---------------------|-------------------|
| AC1 | <measurable statement, e.g. "<metric> on <dataset> is at least <threshold>"> | <script, test, or inspection that determines pass/fail> | D1 |
| AC2 | <criterion> | <verification method> | D2 |

## Open questions

- [ ] Q1: <question>. Owner: <name or role>. Needed before: <phase>.
- [ ] Q2: <question>.
