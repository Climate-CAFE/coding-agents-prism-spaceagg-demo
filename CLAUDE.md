# Claude Code Instructions

@AGENTS.md

## Skills

Project Skills live in `.claude/skills/`. Each `SKILL.md` describes when to use it. Read the applicable Skill before starting a task, and reuse its scripts where available:

- `create-specs`: feature specifications, plans, tasks, and status files with approval gates.
- `raster-processing`: raster metadata inspection, grid alignment checks, and fishnet generation.
- `areal-overlay`: polygon intersections, area measurement, densification, and coverage calculations.
- `weighted-spatial-aggregation`: area-weighted and population-weighted aggregation, missing-data handling, and temporal summaries.
- `snakemake-workflow`: DAG design, incremental reruns, dependencies, and QC failure handling.
- `python-pipeline-style`: Python module structure, configuration, QC, and testing conventions in `src/` and `tests/`. **Required** before creating, modifying, or refactoring Python pipeline code.


## Planning and Execution

- Before planning or implementing any new feature, invoke `create-specs` (via the Skill tool or `/create-specs`) and follow its approval gates.
- Begin each new feature in Plan Mode (select with `Shift+Tab`).
- Use `create-specs` to document the feature's requirements, assumptions, and acceptance criteria.
- Do not implement code until the feature specification is approved.
- Use the relevant scientific Skills during implementation and validation.
- Stop and ask for approval before changing any decision recorded in the feature's `spec.md`.
- Update `specs/NN-<feature>/status.md` with progress, validation results, and outstanding issues before ending a session or using `/clear`.
- Follow the development workflow and scientific guardrails in `AGENTS.md`.
