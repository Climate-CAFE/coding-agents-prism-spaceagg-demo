# Spec: PRISM fishnet, Census block–cell crosswalk, and area weights

## Approval

- **Status:** approved
- **Version:** draft 1 (committed in d55de3b)
- **Last changed:** 2026-10-28
- **Approved by:** project lead, via chat
- **Approved on:** 2026-10-28

## Goal

Build a reusable fishnet of the PRISM 800 m grid cells that cover the configured state, and a block-to-cell crosswalk with area weights. Later features use the weights to aggregate daily PRISM precipitation to Census blocks and counties.

## Findings and reference benchmarks

- The PRISM grid is shared across states and validated in Feature 3 (EPSG:4269, 7025 × 3105, NoData -9999.0).
- Washington reference values, not gates: population 7,705,281 and 39 counties. Fishnet cell count and low-coverage blocks are reported without predefined targets.
- The `raster-processing` fishnet script writes the whole raster as GeoPackage and needs `fiona`. It is reused only for its cell-polygon function and ID formula.
- The `areal-overlay` Skill gives the method (densify, equal-area measurement, sliver removal, weights, coverage). It has no code.

## Scope

**In scope**
- Window of PRISM cells covering the state's blocks, with a configurable margin (2 cells), IDs on the full grid.
- Densify, project to EPSG:5070, intersect, remove slivers, weight, and compute coverage.
- Fishnet and crosswalk as GeoParquet/Parquet, with QC JSON.
- Snakemake rule; Features 1–3 unchanged.

**Out of scope**
- Population or precipitation aggregation to blocks or counties (later feature).
- Geometry repair. Invalid geometries fail the run.
- Other states' reference values.

## Key decisions

| ID | Decision |
|----|----------|
| D1 | Source grid: reference raster = first configured PRISM date of the first configured year, read through Feature 3's inspection (`/vsizip/`). Requires that year's Feature 3 `raster_validation.csv` with no issues. Other years reuse the fishnet and crosswalk only if their reference raster grid is identical (`validate_same_grid`, no issues). |
| D2 | Window: the bounding box of the state's blocks (EPSG:4269) mapped to raster rows and columns, expanded by `fishnet_margin_cells: 2`, clipped to the raster. Only window cells are generated. |
| D3 | Cell ID = `row * raster_width + col + 1` on the full grid. Cell polygons from the full affine transform, using a local copy of the Skill's `cell_polygon()` logic in `src/crosswalk.py` (Rasterio and Shapely; Fiona not installed). The Skill script is not modified. |
| D4 | Densify both blocks and cells by `densify_deg: 0.0001` in EPSG:4269, then project to `area_crs: EPSG:5070`. |
| D5 | Intersect in EPSG:5070. Exclude overlaps with area ≤ `min_overlap_m2: 10`; record the count and total area removed. |
| D6 | `area_weight = overlap_area / sum(retained overlaps of the block)`. Weights sum to 1 within `weight_tol: 1.0e-9`. |
| D7 | `block_coverage = sum(retained overlaps) / block area` in EPSG:5070. Coverage below `low_coverage_threshold: 0.99` is a warning, not a failure. |
| D8 | Crosswalk columns: `block_geoid`, `county_geoid`, `cell_id`, `population` (original block total, not allocated; allocation happens in Feature 5), `overlap_area_m2`, `area_weight`, `block_coverage`. Regular Parquet, no intersection geometries. |
| D9 | Essential QC (failure stops publication): unique `cell_id` in the fishnet; unique (`block_geoid`, `cell_id`) pairs; weights sum to 1 per block; population from the crosswalk's unique blocks equals the Census total; no block with population > 0 lacks crosswalk rows. |
| D10 | Warning QC: blocks below coverage threshold (count and list in QC JSON). |
| D11 | Outputs: `data/intermediate/crosswalk/{vintage}/{state_fips}/fishnet.parquet` (GeoParquet) and `block_cell_crosswalk.parquet` (Parquet); QC at `data/metadata/crosswalk/{vintage}/{state_fips}/qc_report.json`. Written atomically; failed QC publishes nothing. |
| D12 | Snakemake: rule per vintage and state, inputs = Feature 2 `blocks.parquet` and Feature 3 `raster_validation.csv`. Reruns only when inputs change. |
| D13 | Config in Hydra: `fishnet_margin_cells`, `densify_deg`, `area_crs`, `min_overlap_m2`, `weight_tol`, `low_coverage_threshold` in `conf/crosswalk.yaml`; state and vintage from `conf/census.yaml`. |

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | Fishnet cell IDs are unique and follow `row * width + col + 1` on the full grid. | Offline test; real run. |
| AC2 | Crosswalk (`block_geoid`, `cell_id`) pairs are unique. | Offline test; real run. |
| AC3 | Weights sum to 1 within tolerance for each block with retained overlaps. | Offline test; real run. |
| AC4 | Population from the crosswalk's unique blocks equals the Census total. | Real run (7,705,281). |
| AC5 | A populated block with no crosswalk rows fails the run and publishes nothing. | Offline test. |
| AC6 | Blocks below 99% coverage are listed as warnings and the run succeeds. | Offline test; real run (reference: 2). |
| AC7 | Fishnet cell count is reported; no predefined count is assumed or compared. | Real run; informational. |
| AC8 | Feature 1–3 outputs and original inputs are unchanged. | SHA-256 and mtime check. |
| AC9 | Rerun with unchanged inputs runs no jobs. | `snakemake -n`. |
| AC10 | All parameters in Hydra config, not code. | Grep audit. |

## Open questions

- [x] Q1: Densify both blocks and cells (D4). Answered 2026-10-28.
- [x] Q2: Keep the original block population (D8). Answered 2026-10-28.
- [x] Q3: Do not install Fiona; use a local copy of `cell_polygon()` in `src/crosswalk.py` (D3). Answered 2026-10-28.
- [x] Q4: Use the first configured PRISM year's grid; reuse for other years only when validated identical (D1). Answered 2026-10-28.
