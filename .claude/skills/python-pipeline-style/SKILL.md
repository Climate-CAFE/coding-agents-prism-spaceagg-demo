---
name: python-pipeline-style
description: Use when writing, modifying, testing, or refactoring Python pipeline scripts. Covers simple code structure, Hydra configuration, Parquet/DuckDB processing, QC, logging, and pytest conventions.
---

# Python Pipeline Style

Project-wide instructions, scientific guardrails, and approval requirements are defined in `AGENTS.md`.

Keep Python code simple, readable, modular, and easy to maintain. Avoid overengineering.

## Code Structure

- Keep pipeline scripts in `src/` and tests in `tests/`.
- Organize scripts by processing stage, with clear inputs and outputs.
- Prefer small functions over classes or unnecessary abstractions.
- Add shared helpers only when they are actually needed.
- Keep QC functions and QC reporting in `src/qc.py`.
- Separate scientific calculations from entry points so they can be tested independently.
- Reuse existing functions instead of duplicating logic.

## Data Processing

- Use Parquet for intermediate and final tabular datasets.
- Prefer DuckDB for querying, filtering, joining, and aggregating Parquet files.
- Use Rasterio, GeoPandas, and Shapely for raster and spatial operations.
- Use Pandas and NumPy when they make processing simpler.
- Process data by state, date, or year when appropriate.
- Reuse existing outputs rather than repeating expensive processing.
- Keep schemas, geographic identifiers, and scientific units consistent.
- Write outputs atomically using temporary files and rename them after successful completion.
- Avoid introducing persistent databases or unnecessary processing frameworks.

## Hydra Configuration

- Use Hydra for pipeline configuration.
- Each executable pipeline stage should use `@hydra.main` with `main(cfg: DictConfig)`.
- Read paths, states, dates, years, and scientific parameters from configuration.
- Use `pathlib.Path` for filesystem paths.
- Avoid hardcoded paths, dates, and state-specific values.
- Keep configuration handling consistent across scripts.

Example:

```python
import hydra
from omegaconf import DictConfig


def process(cfg: DictConfig) -> None:
    """Run the processing stage."""
    ...


@hydra.main(
    config_path="../conf",
    config_name="config",
    version_base=None,
)
def main(cfg: DictConfig) -> None:
    process(cfg)


if __name__ == "__main__":
    main()
```

## QC and Logging

- Keep QC checks and reporting in `src/qc.py`.
- Call relevant QC functions from each processing stage.
- Write QC results separately from scientific datasets.
- Check row counts, uniqueness, missingness, and scientific calculations where relevant.
- Keep scientific thresholds configurable.
- Record relevant validation results, warnings, errors, and provenance.
- Raise clear errors when critical validation checks fail.
- Do not leave incomplete outputs that appear valid after a failed run.
- Use Python `logging` instead of `print()` in pipeline scripts.

## Testing

- Use pytest with small synthetic datasets that run offline.
- Keep tests short, readable, and focused on one behavior at a time.
- Test scientific calculations using simple, manually verifiable expected values.
- Cover important edge cases, including missing data and invalid inputs.
- Check output schemas and QC results where relevant.
- Avoid unnecessary fixtures, mocking, parametrization, or complex test frameworks.
- Keep tests independent of large downloads and HPC resources.
- Run relevant tests after changes and report failures.

## Workflow and Refactoring

- Let Snakemake manage dependencies and execution order.
- Keep Python scripts responsible for processing their declared inputs and writing outputs.
- Preserve existing scientific methods, units, date conventions, and QC requirements during refactoring.
- Compare scientific results before and after refactoring using known-answer tests and numerical tolerances.
- Avoid modifying unrelated stages or introducing unnecessary abstractions.
- Consult relevant scientific Skills for domain-specific calculations.
- Follow the approval workflow in `AGENTS.md`.
