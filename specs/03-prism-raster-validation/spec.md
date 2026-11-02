# Spec: PRISM raster inspection and validation

## Approval

- **Status:** approved
- **Version:** draft 1 (committed in d55de3b)
- **Last changed:** 2026-10-28
- **Approved by:** project lead, via chat
- **Approved on:** 2026-10-28

## Goal

Check that each downloaded daily PRISM precipitation raster in the Feature 1 ZIPs is readable and sits on the same grid as a reference raster. Record the result per date so later features can rely on the grid. Report only; never change the rasters.

## Findings from inspection

- Each ZIP holds a GeoTIFF (`prism_ppt_us_30s_YYYYMMDD.tif`) plus sidecars: `.prj`, `.aux.xml`, `.info.txt`, `.stx`, `.stn.csv`, `.xml`. The format is GeoTIFF, not BIL.
- `.info.txt` names the source dataset as `.bil`, so the GeoTIFF is a converted copy. Recorded for provenance.
- The CRS is GCS North American 1983 (from `.prj`). This is the grid reference for the CRS check.
- `rasterio` is not installed in `prism-spaceagg`. Reading in place requires it (Q1).

## Scope

**In scope**
- Read each configured date's `.tif` directly from its ZIP via `/vsizip/`. No extraction.
- Per-date checks against a reference raster: readable, CRS, dimensions, affine transform, resolution and bounds (derived from the transform), rotation, NoData.
- `raster_validation.csv` in the metadata directory, one row per expected date.
- Snakemake rule that depends on Feature 1's manifest. Incremental.

**Out of scope**
- Resampling, reprojection, or any change to the rasters.
- Value checks (precipitation ranges, NoData counts per raster).
- Temporal alignment to local calendar days (documented only, later feature).
- Feature 1 download and Feature 2 Census outputs.

## Key decisions

| ID | Decision |
|----|----------|
| D1 | Read in place from `data/raw/prism/ppt/<year>/<zip>` through `/vsizip/`. Member = the single `.tif` in the ZIP. |
| D2 | Reference raster = the first expected date (from Feature 1 `expected_dates`), not the first readable date. |
| D3 | Exact checks: driver GTiff; CRS equal to the reference; width and height equal. |
| D4 | Transform check: each of the six affine coefficients within `prism.transform_tol` (1.0e-9) of the reference. Resolution and bounds are derived from the transform, so they are covered by this check. |
| D5 | Rotation: a non-zero `b` or `d` term (beyond tolerance) is flagged `rotated_transform`. |
| D6 | NoData is read from the first configured raster and used as the reference for later dates. A date whose NoData is missing gets `nodata_missing`; a different value gets `nodata_mismatch`. A reference with no NoData is `invalid_reference_metadata`. |
| D7 | Issue codes: `missing_file`, `unreadable`, `invalid_reference_metadata`, `rotated_transform`, `crs_mismatch`, `shape_mismatch`, `transform_mismatch`, `nodata_missing`, `nodata_mismatch`. Joined with `;`. |
| D8 | `matches_reference`: `TRUE` if the date is readable and has no grid issue; `FALSE` if it has one; blank if the comparison is impossible (missing or unreadable date, or invalid reference). |
| D9 | Invalid reference (unreadable, rotated, or missing CRS): every row gets `invalid_reference_metadata` and blank `matches_reference`. |
| D10 | Output: `data/metadata/prism/ppt/<year>/raster_validation.csv`, written atomically. |
| D11 | Reuse by import, not copy: `inspect_raster` and `validate_same_grid` from `.claude/skills/raster-processing/scripts/`; `expected_dates` from Feature 1. |
| D12 | Snakemake: rule `validate_prism_rasters` per year. Input = Feature 1 `manifest.csv`, so it reruns only when that manifest changes. No download or Census rerun. |
| D13 | Report-only: all issues, including raster metadata mismatches, are recorded in the CSV and exit 0. The run fails only if the CSV cannot be written. |

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | `raster_validation.csv` has one row per expected date. | Offline test; real run (366 rows for 2024). |
| AC2 | The reference is the first configured date. | Offline test with a reference-date mismatch. |
| AC3 | Each injected problem yields its issue code: missing file, unreadable file, rotated transform, CRS, shape, transform, NoData. | Offline tests on synthetic ZIPs. |
| AC4 | `matches_reference` is blank when the comparison is impossible. | Offline test with an invalid reference. |
| AC5 | Real 2024 run: all 366 readable; `matches_reference` TRUE for all; no issues. | Real run. |
| AC6 | Original ZIPs unchanged (SHA-256 and mtime). | Before and after comparison. |
| AC7 | Rerun with unchanged manifest runs no jobs. | `snakemake -n`. |
| AC8 | `transform_tol` and all paths are in Hydra config, not code. | Grep audit. |

## Open questions (resolved)

- [x] Q1: Install `rasterio` from conda-forge into `prism-spaceagg` and add it to `environment.yaml`. Answered 2026-10-28.
- [x] Q2: Import `inspect_raster` and `validate_same_grid` by path; no copy. Answered 2026-10-28.
- [x] Q3: Report-only; exit 0 for raster metadata mismatches (D13). Answered 2026-10-28.
- [x] Q4: NoData read from the first configured raster and used as reference (D6). Answered 2026-10-28.
