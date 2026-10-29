# Spec: Daily population-weighted county precipitation

## Approval

- **Status:** approved
- **Version:** draft 1 (uncommitted)
- **Last changed:** 2026-10-28
- **Approved by:** project lead, via chat
- **Approved on:** 2026-10-28

## Goal

For each county in the configured state and year, compute the population-weighted daily precipitation from PRISM 800 m rasters, with block-level and county-level missing-data coverage. Later features use these county-day series.

## Findings

- Rasters are float32 GeoTIFFs inside the Feature 1 ZIPs, NoData -9999.0, EPSG:4269 (Feature 3). Sampled values on 2024-01-01 range 0 to 1.77, with no negatives.
- The units are not stated in the GeoTIFF or XML metadata. Q1 asks for confirmation that the values are millimeters.
- The crosswalk (Feature 4) holds block–cell pairs with `area_weight` (normalized over all retained overlaps) and `block_coverage`.

## Scope

**In scope**
- Per date, read only the raster window the crosswalk needs, directly from the ZIP (`/vsizip/`).
- Block precipitation = area-weighted mean of valid intersecting cells; county precipitation = population-weighted mean of valid blocks.
- Daily county Parquet with coverage columns, for each configured year.
- Essential QC; Snakemake rule with incremental inputs.

**Out of scope**
- Temporal alignment of the PRISM day (24 h ending 12:00 UTC) to local calendar days. Documented; not corrected (Q2).
- Annual totals or means (later feature).
- Gap filling or imputation.
- Other PRISM variables.

## Key decisions

| ID | Decision |
|----|----------|
| D1 | Read each date's GeoTIFF from its Feature 1 ZIP through `/vsizip/`; never extract or modify. Dates from Feature 1 `expected_dates`. |
| D2 | Read only the window of the full raster that the crosswalk's `cell_id` values need. Derive row and column from `cell_id` with `width` from the full raster: `row = (cell_id - 1) // width`, `col = (cell_id - 1) % width`. |
| D3 | A raster value equal to NoData is missing. Missing cells are excluded from their block. |
| D4 | Block precipitation: `p_block = sum(w_valid * x) / sum(w_valid)` over valid cells, where `w` is the crosswalk `area_weight`. Renormalized within the block. |
| D5 | Block coverage for the day: `sum(w_valid)` over all of that block's cells (0 to 1). |
| D6 | A block with no valid cells is missing for that day (its population is not used). |
| D7 | County precipitation: `P = sum(pop_b * p_b) / sum(pop_b)` over blocks with a valid `p_b`. |
| D8 | County output columns: `county_geoid`, `date`, `precip_mm`, `population_total`, `population_valid`, `population_coverage`. A county with no valid population gets a blank `precip_mm` and coverage 0. |
| D9 | Population is the original Census block population (Feature 2), used as the weight. |
| D10 | Output: `data/output/prism_county_daily/{vintage}/{state_fips}/county_daily_{year}.parquet`, written atomically. Units: millimeters (`precip_mm`), based on PRISM's documented units; the units are not recorded in the raster metadata. |
| D11 | Essential QC (failure stops publication): valid precipitation (finite and ≥ 0 where present); county coverage (every county in the crosswalk appears for every date); no duplicate `county_geoid`–`date`; the dates equal the expected dates for the year. A missing or unreadable raster fails the run; no date is skipped and no incomplete result is published. |
| D12 | Snakemake: rule per vintage, state, and year. Inputs: Feature 4 crosswalk outputs, Feature 3 `raster_validation.csv` for the year, and the Feature 1 manifest. Rebuilds only when inputs or recorded settings change. |
| D13 | Hydra: years from `prism.years`; settings in `conf/aggregation.yaml`; paths in `conf/datapaths.yaml` (`output_root: data/output`). |
| D14 | Time: each row keeps the PRISM file date. The source day is the 24 hours ending 12:00 UTC; no local-day shift is applied. This is documented in the output metadata. |
| D15 | Expected rows are derived at run time: expected dates (Feature 1 `expected_dates`) × counties in the crosswalk. Not hardcoded. For Washington 2024 this is 14,274 (366 × 39), used as a reference count only. |

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | Block precipitation equals the hand-calculated weighted mean on a synthetic grid. | Offline test. |
| AC2 | A NoData cell is excluded and the remaining weights are renormalized, with coverage below 1. | Offline test. |
| AC3 | A county whose blocks all lack valid data gets a blank value and coverage 0. | Offline test. |
| AC4 | County output has one row per county per expected date, with no duplicates. | Offline test; real run. |
| AC5 | Real 2024 run: row count equals the derived expected count (reference: 14,274); all values finite and ≥ 0; population coverage reported per row. | Real run. |
| AC6 | Original ZIPs and Features 1–4 outputs unchanged. | SHA-256 and mtime. |
| AC7 | Rerun with unchanged inputs plans nothing; changing a setting or code rebuilds only Feature 5. | `snakemake -n`; dry run after a settings change. |
| AC8 | All settings in Hydra config; no hardcoded paths or values in code. | Grep audit. |

## Open questions (resolved)

- [x] Q1: Units are millimeters per PRISM documentation; not recorded in raster metadata. Answered 2026-10-28.
- [x] Q2: Document the 24 h ending 12:00 UTC timing; no local-day shift; keep the PRISM file date. Answered 2026-10-28.
- [x] Q3: Output under `data/output/`. Answered 2026-10-28.
- [x] Q4: Missing or unreadable required rasters fail the run. Answered 2026-10-28.
