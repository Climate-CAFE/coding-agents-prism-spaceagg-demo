---
name: snakemake-workflow
description: Use when creating, modifying, or debugging Snakemake workflows with configuration-driven targets, Python processing stages, wildcard dependencies, and QC.
---

# Snakemake Workflow

Use Snakemake to orchestrate Python processing stages. Keep workflows simple, readable, and configuration-driven. Follow `AGENTS.md` and `python-pipeline-style`.

## Configuration and Targets

- Load pipeline configuration at the beginning of the Snakefile, using Hydra when applicable.
- Read paths, processing years, dates, and geographic settings from configuration.
- Use `expand()` to generate requested final outputs in `rule all`.
- Support multiple processing units through configuration without changing workflow code.

## Rules and Dependencies

- Use one rule per meaningful processing stage.
- Declare inputs, outputs, and log files explicitly.
- Use wildcards for independent units such as years, dates, or regions.
- Keep processing logic in Python scripts under `src/`.
- Execute scripts through `shell:` with relevant Hydra overrides.
- Use simple input functions when dependencies vary by wildcard.
- Reuse shared inputs and intermediate outputs instead of recomputing them.
- Avoid unnecessary wrappers or complex rule abstractions.

## Execution and QC

- Use `snakemake -n` to inspect the execution plan.
- Use `--rerun-incomplete` when recovering interrupted jobs.
- Track scientific parameters that affect outputs so changes trigger appropriate reruns.
- Ensure critical QC failures stop downstream jobs.
- Declare required outputs and keep incomplete files from appearing valid.

## Validation

- Test the DAG with a small subset of processing units.
- Verify correct dependencies and expected outputs.
- Confirm new units generate the necessary jobs.
- Confirm unchanged outputs are skipped and relevant changes trigger reruns.
- Preserve existing output conventions when modifying rules.
