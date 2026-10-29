# Project Instructions

## Project

Build a reproducible and modular Python pipeline to calculate daily population-weighted PRISM 800 m precipitation estimates for U.S. counties using Census block boundaries and population data, and aggregate daily estimates into annual county-level precipitation summaries.

Use Washington State and the year 2024 as the initial demonstration and validation example, but design the pipeline to support multiple years, configurable date ranges, and other U.S. states without modifying scientific processing code.

This repository also demonstrates how coding agents can support scientific software development through project instructions, reusable Skills, lightweight specifications, automated workflows, and scientific validation.

Develop one user-requested feature at a time.

## Tech Stack and Configuration

- Use Python with Rasterio, GeoPandas/Shapely, Pandas/NumPy, and pytest as needed.
- Orchestrate pipeline steps with Snakemake and manage configuration with Hydra (`conf/`).
- Use `@hydra.main` entry points with `main(cfg: DictConfig)` for pipeline stages.
- Configure states, years, dates, paths, and scientific parameters through YAML rather than hardcoding them.
- Create and maintain a Conda environment named `prism-spaceagg` using `environment.yaml`.
- Add all required packages with appropriate version constraints to `environment.yaml`.
- Keep implementation in `src/`, tests in `tests/`, and reusable Skills in `.claude/skills/`.

## Scientific Guardrails

- Validate CRS, geometry validity, raster resolution, transforms, and grid alignment before spatial operations. Do not silently reproject, resample, or change geographic vintages.
- Treat NoData as missing, not zero. Explicitly define coverage thresholds, weighting methods, and normalization.
- Use population-weighted county precipitation estimates derived from Census blocks and PRISM raster intersections.
- Do not hardcode Washington-specific CRS (example), geographic boundaries, coverage thresholds, or reference values. Keep state-specific scientific parameters configurable.
- PRISM daily precipitation covers the 24 hours ending at 12:00 UTC. Document temporal alignment before joining to local-calendar-day datasets.
- Record PRISM source stability status, download date, and checksum.
- Preserve original files in `data/raw/`, intermediate results in `data/intermediate/`, and validated outputs in `data/output/`. Keep paths configurable.
- Separate state-specific Census inputs, crosswalks, and county outputs. Reuse shared PRISM raster data where appropriate.
- Calculate annual precipitation estimates from validated daily county data. Clearly distinguish mean daily precipitation (mm/day) from annual totals (mm), and report missingness and completeness in separate QC outputs. Never treat missing values as zero.
- Report valid days, expected days, missingness, and completeness. Never treat missing precipitation as zero.
- Validate spatial weights, geographic mappings, population coverage, and output uniqueness. Use state-specific QC reference values when available.

## Coding Agent Workflow

- Follow `AGENTS.md` as the shared source of project instructions across coding agents.
- Consult relevant reusable Skills before implementing scientific or technical tasks.
- Before modifying Python pipeline code in `src/` or `tests/`, consult the `python-pipeline-style` Skill.
- Use the `create-specs` Skill before planning or implementing new features, following its specification, plan, tasks, status, and approval workflow.
- Keep specifications lightweight and scoped to the requested feature.
- Preserve scientific decisions and document approved changes rather than silently modifying methods.
- Reuse validated scientific logic and existing scripts where appropriate; avoid unnecessary abstractions or duplicated code.
- Write focused tests and run relevant scientific QC checks.
- Keep code readable, modular, and reproducible.

## Development Workflow

- Implement one approved feature at a time without modifying unrelated files.
- Define requirements, assumptions, expected outputs, and acceptance criteria before implementation.
- Ask for clarification before making methodological decisions.
- Summarize changed files, assumptions, validation results, and outstanding issues after each feature.
- Report tests that could not run and explain why.
- Ask before destructive operations, large downloads or computations, installing packages, or making Git commits.
- Do not commit changes without explicit approval.