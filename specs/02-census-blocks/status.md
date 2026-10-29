# Status: Census block boundaries and population (2020, Washington)

- **Last updated:** 2026-10-28
- **Current phase:** complete (T01–T09 done)
- **Completed on:** 2026-10-28

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | approved | project lead, via chat | 2026-10-28 |
| plan.md | approved | project lead, via chat | 2026-10-28 |
| tasks.md | complete | — | — |
| packages (geopandas, pyogrio, pyarrow) | installed | project lead, via chat | 2026-10-28 |
| TIGER ZIP download (~204 MB) | downloaded | project lead, via chat | 2026-10-28 |

## Results

- Output: `data/intermediate/census/2020/53/blocks.parquet`, 158,093 blocks, population 7,705,281, 39 counties, CRS EPSG:4269.
- QC: `data/metadata/census/2020/53/qc_report.json`, status `pass`, both reference checks `pass`.
- Source ZIP SHA-256 recorded in QC JSON: `0ccdbb2b58d4cdc083097411d791ba7a61e599f0937073187617f76740c61689`.

## Blockers

None.

## Deviations

- Feature 2 `census.state_fips` override arrives as an integer from Hydra; the script normalizes it to a two-digit string.
- Snakemake reports missing provenance for `download_prism_ppt` because `.snakemake/` was deleted earlier. Outputs are present and up to date. Left as is by decision; Feature 1 outputs were not modified.

## Validation results

| ID | Status | Evidence |
|----|--------|----------|
| AC1 | passing | raw ZIP at configured path; SHA-256 in QC JSON; `check_zip` passes |
| AC2 | passing | exact six columns, verified independently |
| AC3 | passing | `block_geoid` unique; 158,093 rows equal source |
| AC4 | passing | population int64, no nulls, no negatives |
| AC5 | passing | 0 invalid geometries; CRS EPSG:4269 equals source |
| AC6 | passing | population 7,705,281 and 39 counties; mismatch test publishes nothing |
| AC7 | passing (test) | reference-skipped branch exercised via config; `check_reference` returns `skipped` when unset |
| AC8 | passing | `snakemake -n`: nothing to be done; PRISM job unchanged |
| AC9 | passing | grep audit clean |
| AC10 | passing | 3 Census tests in `tests/test_census_blocks.py` |

## Next steps

None. Feature 2 is complete.

The PRISM provenance metadata is left as is by decision; no `snakemake --touch` and no Feature 1 output changes.
