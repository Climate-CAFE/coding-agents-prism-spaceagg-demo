# Plan: Daily population-weighted county precipitation

- **Spec:** `specs/05-county-daily-precip/spec.md` (draft 1, approved 2026-10-28)
- **Status:** approved 2026-10-28, via chat (change: no `conf/aggregation.yaml`; units and day definition recorded in output metadata)

## Approach

One Hydra-configured script processes one year. For each expected date it reads the crosswalk's raster window from the ZIP, computes block means over valid cells, then county means over valid blocks. Results accumulate in memory (14,274 rows for WA 2024), are checked by QC, and are published atomically to `data/output/`. Feature 3 validation and the Feature 4 crosswalk are required inputs.

## Layout

```
conf/datapaths.yaml            # ADD output_root: data/output
src/county_precip.py           # NEW: window read, block and county means, publish
src/qc.py                      # ADD "Feature 5: county daily precipitation" section
Snakefile                      # ADD aggregate_county_daily rule and targets (Features 1–4 unchanged)
tests/test_county_precip.py    # NEW: 3 synthetic tests
```

No new packages.

## Modules

1. **Config** — no new file. Units (`mm`) and the day definition (24 h ending 12:00 UTC) are fixed conventions, held as constants in `src/county_precip.py` and written to the Parquet metadata and QC JSON. Paths and years use the existing Hydra config.
2. **Inputs** — `expected_dates` (Feature 1), `require_validated_year` and `reference_grids` (Feature 4 crosswalk module, reused by import). Crosswalk parquet and Census block populations come from the crosswalk table itself.
3. **Window** — `county_precip.cell_window(cell_ids, width)`: derive `row = (cell_id - 1) // width` and `col = (cell_id - 1) % width` for every crosswalk row (D2), then the min and max row and column give one window.
4. **Read** — `read_window(zip_path, window)`: open `/vsizip/…/*.tif` with rasterio and read only that window. Missing or unreadable file raises (D11).
5. **Block means** — `block_precip(crosswalk, values, nodata)`: each row's value = window array at (row, col); valid = finite and not NoData. Per block: `sum(w·x)/sum(w)` over valid rows (D4); coverage = `sum(w)` over valid rows (D5); no valid rows → NaN (D6).
6. **County means** — per county: `sum(pop·p)/sum(pop)` over blocks with valid `p` (D7); `population_total` and `population_valid` from unique blocks; coverage = valid / total (D8). Counties with no valid population → NaN, coverage 0.
7. **Output** — one row per county per expected date with the D8 columns and PRISM file date (D14). Expected rows = dates × counties (D15). Written as Parquet via `.tmp` and rename.
8. **QC** — `src/qc.py` Feature 5 section, essential only: finite and ≥ 0 where present; row count equals expected; no duplicate county–date; dates equal expected; every county present each date. Failure raises and publishes nothing.
9. **Workflow** — `Snakefile`: rule `aggregate_county_daily` with wildcards `vintage`, `state_fips`, `year`. Each run keeps the full `prism.years` list (so the Feature 4 grid check covers every year) and selects its year with `+year=`. Inputs: crosswalk parquet and QC JSON (Feature 4), Feature 3 `raster_validation.csv` for the year, Feature 1 `manifest.csv` for the year, and the config and code files. Params: sha256 content hashes of `src/county_precip.py`, `src/qc.py`, `src/crosswalk.py`, `conf/census.yaml`, `conf/prism_ppt.yaml`, `conf/crosswalk.yaml`, so content changes trigger a rebuild (as in Feature 4).
10. **Tests** — `tests/test_county_precip.py`, three synthetic tests:
    - weighted mean of two blocks in one county matches a hand calculation;
    - a NoData cell is excluded, the remaining weights renormalize, and block coverage is below 1;
    - a county with no valid blocks gets a blank value and coverage 0, and a missing raster raises.

## Skills applied

- **raster-processing:** window reading and cell-to-row/column formula (formula from the Skill's guardrails, cross-checked against Feature 4).
- **weighted-spatial-aggregation:** population-weighted aggregation, missing-data handling, coverage (guidance only).
- **python-pipeline-style:** Hydra entry point, `pathlib`, logging, QC in `qc.py`, pytest.
- **snakemake-workflow:** wildcard rule, declared outputs, content-hash params.

## Configuration

| Parameter | Value | File | Decision |
|-----------|-------|------|----------|
| Years | from `prism.years` | `prism_ppt.yaml` | D13 |
| Units | `mm` (fixed convention; recorded in metadata) | `county_precip.py` constant | D10 |
| Day definition | 24 h ending 12:00 UTC (fixed; recorded in metadata) | `county_precip.py` constant | D14 |
| Output root | `data/output` | `datapaths.yaml` | D10 |
| Vintage, state | 2020, `"53"` | `census.yaml` | D13 |

## Data manifest

| Dataset | Version | Location | Transformations | Stage |
|---------|---------|----------|-----------------|-------|
| PRISM daily ppt GeoTIFF | Feature 1 download | inside `data/raw/prism/ppt/<year>/*.zip` | None (read window only) | aggregation |
| Block–cell crosswalk | Feature 4 | `data/intermediate/crosswalk/2020/53/block_cell_crosswalk.parquet` | Read only | aggregation |
| County daily precipitation | per run | `data/output/prism_county_daily/2020/53/county_daily_2024.parquet` | Block and county means | output |
| QC report | per run | `data/metadata/prism_county_daily/2020/53/county_daily_2024_qc.json` | None | QC |

## Traceability

| Spec item | Element | Task |
|-----------|---------|------|
| D1 | `read_window` | T03 |
| D2 | `cell_window` | T03 |
| D3 | valid mask in block means | T04 |
| D4, D5, D6 | `block_precip` | T04 |
| D7, D8, D9 | county means | T05 |
| D10 | output step | T06 |
| D11 | QC and read failures | T02, T06 |
| D12 | `Snakefile` rule | T07 |
| D13 | Hydra config (paths, years) | T01 |
| D14 | Parquet and QC metadata | T06 |
| D15 | expected count in QC | T02 |
| AC1 | block mean test | T07 |
| AC2 | NoData renormalization test | T07 |
| AC3 | blank county test | T07 |
| AC4 | QC row and duplicate checks | T05, T07 |
| AC5 | real 2024 run | T08 |
| AC6 | checksums and mtimes | T08 |
| AC7 | `snakemake -n` after changes | T08 |
| AC8 | config audit | T08 |

## Validation

- **Tests:** `pytest` in `prism-spaceagg`, including the 14 existing tests.
- **Real run:** Washington 2024. Row count equals the derived expected count (reference 14,274). Values finite and ≥ 0. Spot-check three counties by hand from block-level values.
- **Originals:** ZIP SHA-256 against the Feature 1 manifest; mtimes unchanged.
- **Incremental:** rerun plans nothing; a settings change plans only `aggregate_county_daily`.

## Risks

| Risk | Mitigation |
|------|------------|
| 366 window reads from compressed GeoTIFFs are slow | Read only the crosswalk window; time the run. |
| A county with a few tiny blocks gets noisy means | Coverage reported per row; no threshold applied (spec). |
| Raster grid differs from the crosswalk grid | Feature 3 validation required before this rule runs. |

## Alternatives considered

- Load all rasters at once: rejected; one date at a time (spec).
- Skip missing dates: rejected; failure (D11).
