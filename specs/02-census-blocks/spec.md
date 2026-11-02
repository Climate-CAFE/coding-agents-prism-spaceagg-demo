# Spec: Census block boundaries and population (2020, Washington)

## Approval

- **Status:** approved
- **Version:** draft 1 (committed in d55de3b)
- **Last changed:** 2026-10-28
- **Approved by:** project lead, via chat
- **Approved on:** 2026-10-28

## Goal

Create a cleaned, validated GeoParquet of 2020 Census blocks for Washington (FIPS `53`), with each block's 2020 population (`POP20`), as the block input for later population-weighted county precipitation. Vintage, state, source, CRS, and reference totals are configured, so other states and vintages need no code change.

## Scope

**In scope**
- Download `tl_2020_53_tabblock20.zip` (TIGER/Line 2020 `TABBLOCK20`, about 204 MB) and keep it unmodified.
- Write `data/intermediate/census/2020/53/blocks.parquet` with columns `state_fips`, `county_geoid`, `block_geoid`, `population`, `geometry`, `vintage`.
- Write a QC JSON report and publish the GeoParquet only if essential checks pass.
- Hydra config in `conf/census.yaml`; base paths in `conf/datapaths.yaml`; one Snakefile rule.
- Reuse Feature 1's `fetch_file`, `check_zip`, and `check_size`.

**Out of scope**
- Reprojection or CRS change. The data stay in their source CRS.
- Other block attributes (housing, land area, water area).
- Block-to-PRISM intersection, weights, and county aggregation (later features).
- Other states and vintages beyond configuration. Their reference totals are not supplied.

## Key decisions

| ID | Decision |
|----|----------|
| D1 | Source: `https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_53_tabblock20.zip`, built from config fields `vintage`, `state_fips`, and `base_url`. |
| D2 | `population` = `POP20` as published (2020 Census counts). Null or negative values are errors. |
| D3 | `block_geoid` = `GEOID20` (15 digits). `county_geoid` = `STATEFP20` + `COUNTYFP20` (5 digits). `state_fips` = configured FIPS. |
| D4 | No reprojection. The file's CRS must equal the configured `expected_crs`; otherwise the run fails. |
| D5 | Essential checks (failure stops publication): required columns present; `block_geoid` unique; population nonnull and nonnegative; all geometries valid; CRS matches. |
| D6 | Reference checks: total population and county count, from config for the vintage and state. A mismatch is an essential failure. If no reference is configured, the check is skipped with a logged warning and recorded as `skipped` in the QC report. |
| D7 | Publication: write to `.tmp`, then rename, only after essential checks pass. A failed run leaves no `blocks.parquet`. |
| D8 | Paths: raw ZIP at `data/raw/census/{vintage}/{state_fips}/`; GeoParquet at `data/intermediate/census/{vintage}/{state_fips}/`; QC JSON at `data/metadata/census/{vintage}/{state_fips}/qc_report.json`. |
| D9 | Download: reuse Feature 1 `fetch_file` with retries, pause, and timeout from `conf/census.yaml`. The skip-if-valid rule matches Feature 1. |
| D10 | Snakemake: one rule per vintage and state, with the output set to the GeoParquet and QC JSON. Feature 1 rules are unchanged. |

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | The original ZIP is at the D8 raw path, passes `check_zip`, and its SHA-256 is recorded in the QC JSON. | Test on a synthetic ZIP; real run check. |
| AC2 | The GeoParquet has exactly the six required columns. | Schema check in QC and test. |
| AC3 | `block_geoid` is unique and row count equals the source row count. | QC and test. |
| AC4 | Population is nonnull, nonnegative, and integer. | QC and test. |
| AC5 | All geometries are valid, and the CRS equals `expected_crs`. | QC and test. |
| AC6 | Washington totals: population 7,705,281 and 39 counties. A mismatch fails the run and publishes nothing. | Real run; test with a wrong reference. |
| AC7 | With no reference configured, processing completes, the QC JSON marks the check `skipped`, and a warning is logged. | Test. |
| AC8 | A rerun with unchanged inputs runs no jobs. Feature 1 outputs and jobs are unchanged. | `snakemake -n` after the real run. |
| AC9 | All vintage, FIPS, URL, CRS, and reference values are in `conf/census.yaml`, not code. | Grep audit. |

## Reference values (Washington, 2020)

- Population: 7,705,281 (2020 Census), configured as `reference.population`.
- Counties: 39, configured as `reference.county_count`.

## Open questions (resolved)

- [x] Q1: Expected CRS `EPSG:4269`, verified against the downloaded file. Answered 2026-10-28.
- [x] Q2: Add `geopandas`, `pyogrio`, `pyarrow` to `environment.yaml` and install into `prism-spaceagg`. Answered 2026-10-28.
- [x] Q3: Download the ~204 MB TIGER ZIP. Answered 2026-10-28.
- [x] Q4: Reuse Feature 1 `fetch_file` and utilities through a compatible Census config, without modifying Feature 1. Answered 2026-10-28.
