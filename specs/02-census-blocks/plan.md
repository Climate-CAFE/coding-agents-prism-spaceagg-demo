# Plan: Census block boundaries and population (2020, Washington)

- **Spec:** `specs/02-census-blocks/spec.md` (draft 1, approved 2026-10-28)
- **Status:** awaiting approval (gate 2)

## Approach

One Hydra-configured script downloads the TIGER ZIP, verifies it, reads the shapefile directly from the ZIP, selects and renames columns, runs QC, and publishes the GeoParquet and QC JSON only when essential checks pass. Download uses Feature 1's `fetch_file`, `check_zip`, and `check_size` unchanged. A Census config supplies the keys those functions read (`retries`, `backoff_seconds`, `timeout_seconds`, `pause_seconds`). Feature 1 code and config are not modified.

## Layout

```
conf/census.yaml             # NEW: vintage, state, URL, CRS, reference totals, download keys
conf/datapaths.yaml          # ADD intermediate_root
conf/config.yaml             # ADD census to defaults (Feature 1 reads only cfg.prism and cfg.paths)
src/census_blocks.py         # NEW: download, read, transform, publish
src/qc.py                    # ADD "Feature 2: Census blocks" section
Snakefile                    # ADD census rule and target (Feature 1 rule unchanged)
tests/test_census_blocks.py  # NEW: 3 offline tests
environment.yaml             # ADD geopandas, pyogrio, pyarrow
```

## Modules

1. **Config** — `conf/census.yaml`:
   - `vintage: 2020`, `state_fips: "53"`.
   - `base_url` and `filename` template `tl_{vintage}_{state_fips}_tabblock{yy}.zip`.
   - `expected_crs: EPSG:4269`.
   - `reference: {population: 7705281, county_count: 39}`. Null entries mean the check is skipped.
   - Download keys: `retries: 3`, `backoff_seconds: 2`, `pause_seconds: 0.5`, `timeout_seconds: 300`.
2. **Paths** — `conf/datapaths.yaml` adds `intermediate_root: data/intermediate`. Paths are derived in code from `raw_root`, `intermediate_root`, `metadata_root`, `vintage`, and `state_fips` (D8).
3. **Download** — `census_blocks.fetch_raw_zip`: skip if the raw ZIP passes `check_zip`; otherwise call `fetch_file` (D9).
4. **Transform** — `census_blocks.build_blocks`: `gpd.read_file("zip://...")`; keep `STATEFP20`, `COUNTYFP20`, `GEOID20`, `POP20`, geometry. Build `state_fips`, `county_geoid` (D3), `block_geoid`, `population`, `vintage`. No reprojection (D4).
5. **QC** — `src/qc.py`, Feature 2 section:
   - `check_essential(gdf, expected_crs)` raises `ValueError` for missing columns, duplicate `block_geoid`, null or negative population, invalid geometries, or CRS mismatch.
   - `check_reference(gdf, reference)` returns `skipped` or `pass`/`fail` for population total and county count.
   - `write_json_atomic(report, path)`.
6. **Publish** — write GeoParquet to a `.tmp` file, then rename. Write QC JSON. If essential checks fail, no GeoParquet is written and the run exits non-zero (D5, D7).
7. **Workflow** — `Snakefile`: rule `census_blocks` with wildcards `vintage` and `state_fips`. Outputs: raw ZIP, GeoParquet, QC JSON. Targets come from a `targets` list in `conf/census.yaml` (initially one pair).
8. **Tests** — `tests/test_census_blocks.py`, three tests on a synthetic shapefile written to a ZIP:
   - success: exact columns, row count, QC JSON `pass`.
   - duplicate `GEOID20`: raises, no GeoParquet written.
   - reference population mismatch: raises, no GeoParquet written.

## Skills applied

- **python-pipeline-style:** Hydra entry point, `pathlib`, logging, small functions, QC in `qc.py`, tests.
- **snakemake-workflow:** wildcard rule, declared outputs, failure exit, incremental reruns.
- **weighted-spatial-aggregation** and **areal-overlay:** not used in this feature (no weighting or overlay yet).

## Configuration

| Parameter | Value | File | Decision |
|-----------|-------|------|----------|
| Vintage | 2020 | `census.yaml` | D8 |
| State FIPS | `"53"` | `census.yaml` | D1 |
| Base URL | `https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/` | `census.yaml` | D1 |
| Expected CRS | `EPSG:4269` | `census.yaml` | D4 |
| Population reference | 7,705,281 | `census.yaml` | D6 |
| County reference | 39 | `census.yaml` | D6 |
| Download retries, backoff, pause, timeout | 3, 2 s, 0.5 s, 300 s | `census.yaml` | D9 |
| Raw, intermediate, metadata roots | `data/raw`, `data/intermediate`, `data/metadata` | `datapaths.yaml` | D8 |

## Data manifest

| Dataset | Version | Location | Transformations | Stage |
|---------|---------|----------|-----------------|-------|
| TIGER/Line TABBLOCK20, WA | 2020, Last-Modified 2023-01-06 | `data/raw/census/2020/53/tl_2020_53_tabblock20.zip` | None (unmodified) | download |
| Census blocks | 2020 | `data/intermediate/census/2020/53/blocks.parquet` | Column selection and rename; county GEOID built | transform |
| QC report | per run | `data/metadata/census/2020/53/qc_report.json` | None | QC |

## Traceability

| Spec item | Element | Task |
|-----------|---------|------|
| D1 | `census.yaml` URL template; `fetch_raw_zip` | T02 |
| D2 | `build_blocks` (`POP20` → `population`) | T03 |
| D3 | `build_blocks` (GEOID construction) | T03 |
| D4 | `check_essential` CRS check; no reprojection | T04 |
| D5 | `check_essential`; publish gating | T04, T05 |
| D6 | `check_reference` | T04 |
| D7 | atomic publish in `census_blocks.main` | T05 |
| D8 | path derivation from config | T01, T05 |
| D9 | `fetch_raw_zip` calls `fetch_file` | T02 |
| D10 | `Snakefile` rule and target | T06 |
| AC1 | download and `check_zip`; SHA-256 in QC JSON | T02, T07 |
| AC2–AC5 | `check_essential` | T04, T07 |
| AC6 | `check_reference`; real run | T04, T07 |
| AC7 | `check_reference` skipped branch | T04, T07 |
| AC8 | Snakemake dry run after real run | T06, T07 |
| AC9 | grep audit | T07 |
| AC10 | `tests/test_census_blocks.py` | T07 |

## Validation

- **Tests:** `pytest` in `prism-spaceagg`, including Feature 1's five tests (unchanged).
- **Real run:** Washington 2020. Confirm population 7,705,281, 39 counties, CRS `EPSG:4269`, row count equal to the source, and `snakemake -n` shows no jobs on rerun.
- **Feature 1 check:** `snakemake -n` plans the PRISM job only when its outputs are missing.
- **Grep audit:** no vintage, FIPS, URL, CRS, or reference value in `src/` or `Snakefile` outside `conf/`.

## Risks

| Risk | Mitigation |
|------|------------|
| File read from ZIP fails for an unexpected layout | Check the shapefile's root-level members in the real run; test on a synthetic ZIP with the same layout. |
| Memory use for the full state | Washington block count is about 200k rows, which fits in memory; no chunking. |
| CRS in the file differs from EPSG:4269 | Essential check fails the run and publishes nothing; the value is configurable, not changed silently. |
| Snakemake deletes outputs on failure | Intended: incomplete outputs are not left as valid. |

## Alternatives considered

- Separate Snakemake rules for download and transform: more DAG nodes with no gain for one file. A single rule keeps the raw ZIP as a declared output.
- Extracting the ZIP to disk before reading: unnecessary; geopandas reads from the ZIP directly.
- A new QC module: rejected; Feature 2 checks go in `src/qc.py` as requested.
