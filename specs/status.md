# Status: PRISM 800 m county precipitation pipeline (all features)

- **Last updated:** 2026-10-29
- **Current phase:** Features 1–6 complete. Feature 6 D9 amendment approved 2026-10-29.
- **Scope so far:** Washington State, 2020 Census geography, PRISM 2024 demonstration year.

This file summarizes all features. Per-feature detail lives in `specs/NN-<feature>/status.md`.

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| 01-prism-download: spec, plan, tasks | approved / complete | project lead, via chat | 2026-10-28 |
| 02-census-blocks: spec, plan, tasks | approved / complete | project lead, via chat | 2026-10-28 |
| 03-prism-raster-validation: spec, plan, tasks | approved / complete | project lead, via chat | 2026-10-28 |
| 04-prism-block-crosswalk: spec, plan, tasks | approved / complete | project lead, via chat | 2026-10-28 |
| 05-county-daily-precip: spec, plan (change: no `conf/aggregation.yaml`), tasks | approved / complete | project lead, via chat | 2026-10-28 |
| 06-county-yearly-precip: spec, plan, tasks | approved / complete | project lead, via chat | 2026-10-28 |
| 06 D9 amendment (map CRS, colormap, normalization, boundaries, colorbar label) | approved | project lead, via chat | 2026-10-29 |
| 01 open items: Q1 stability wording, `snakemake` installed via pip, 7.03 GB download total | approved | project lead, via chat | 2026-10-29 |

## Feature summary

| # | Feature | Phase | Completed | Main output |
|---|---------|-------|-----------|-------------|
| 01 | PRISM 800 m daily precipitation download | complete (T00–T10) | 2026-10-28 | 366 daily ZIPs for 2024 in `data/raw/`, manifest with SHA-256 |
| 02 | Census block boundaries and population (2020, WA) | complete (T01–T09) | 2026-10-28 | `data/intermediate/census/2020/53/blocks.parquet`, 158,093 blocks |
| 03 | PRISM raster inspection and validation | complete (T01–T08) | 2026-10-28 | `raster_validation.csv`, 366 of 366 valid |
| 04 | Fishnet, block–cell crosswalk, area weights | complete (T01–T10) | 2026-10-28 | `block_cell_crosswalk.parquet`, 816,566 rows |
| 05 | Daily population-weighted county precipitation | complete (T01–T09) | 2026-10-28 | `county_daily_2024.parquet`, 14,274 rows |
| 06 | Yearly county precipitation and map | complete (T01–T09); map revised 2026-10-29 | 2026-10-28 | `county_yearly_2024.parquet` (39 rows), PNG map |

## Timeline (start to end)

### 2026-10-28

1. **Project setup.** Repository scaffolding: `AGENTS.md`, `CLAUDE.md`, `.claude/skills/`, `conf/` (Hydra), `environment.yaml`, `Snakefile`, `src/`, `tests/`, `specs/`. Conda environment `prism-spaceagg` created.
2. **Feature 1 (PRISM download).** Spec, plan, and tasks approved. Full 2024 download completed: 366 downloaded in run 1, 0 failed; run 2 skipped all 366. Completeness 1.0.
3. **Feature 2 (Census blocks).** TIGER 2020 Washington block ZIP (~204 MB) downloaded. Output has 158,093 blocks, population 7,705,281 (matches the reference), 39 counties, CRS EPSG:4269. QC passed.
4. **Feature 3 (raster validation).** Each ZIP holds a GeoTIFF read via `/vsizip/`. Reference grid is 2024-01-01 (EPSG:4269, 7025 × 3105, NoData −9999.0). All 366 dates valid. `rasterio` 1.5.2 installed.
5. **Feature 4 (crosswalk).** Fishnet of 401,940 cells. Crosswalk of 816,566 rows. Weights sum to 1 per block (max error 2.2e-16). Population through the crosswalk matches the Census total. Three blocks are below 0.99 coverage and reported as warnings.
6. **Feature 5 (daily county precipitation).** 14,274 rows (366 dates × 39 counties). QC passed. Independent check on three dates agrees to 8.9e-16.
7. **Feature 6 (yearly county precipitation and map).** Yearly Parquet (39 rows, 366 days observed for every county). Totals equal the sum of Feature 5 daily means. Map first produced in EPSG:5070 with a blue ramp. After approval, the map was revised .Map changed to EPSG:4269 (original Census CRS, north-up), with no reprojection.
- Colormap: `LinearSegmentedColormap.from_list("blues_light", plt.cm.Blues(np.linspace(0.2, 1, 256)))`.Normalization: `PowerNorm(gamma=0.5, vmin=0, vmax=yearly maximum)`.

## Validation summary

| Feature | Validation | Result |
|---------|-----------|--------|
| 01 | Unit tests; real download manifest; incremental rerun | pass (5 tests); 366/366 SHA-256 match; rerun skips all |
| 02 | Real block data; population and county reference checks | pass; population 7,705,281; 39 counties |
| 03 | Real raster checks against reference grid | pass; 366 of 366 TRUE |
| 04 | Weight sums, population match, unique pairs, low-coverage check | pass; 3 low-coverage blocks warned |
| 05 | Hand-calculation and independent raster recompute | pass; max difference 8.9e-16 |
| 06 | Hand-calculation tests; real-run completeness and sums; PNG checks; Snakemake rerun | pass (20 tests in full suite); 39 rows; means × 366 = totals (max diff 2.3e-13); rerun plans nothing |

Full test suite: 20 pass (`pytest tests`, `prism-spaceagg`).

## Deviations (across features)

- **01:** download total 7.03 GB vs. ~2.8 GB estimate; `snakemake` installed via pip; date range applied as a clip within each year.
- **02:** `census.state_fips` arrives as an integer from Hydra and is normalized to a two-digit string.
- **04:** timestamp changes to config files do not trigger rebuilds; content hashes used instead (`src/crosswalk.py`, `src/qc.py`, `conf/census.yaml`, `conf/prism_ppt.yaml`, `conf/crosswalk.yaml`).
- **05:** no `conf/aggregation.yaml` (approved); Feature 4 rebuilt once due to the `qc.py` hash.
- **06:** figure path includes `{vintage}/{state}` (Snakemake requires shared wildcards); Snakemake params hash only the QC sections each rule uses; D9 amended and approved 2026-10-29.

