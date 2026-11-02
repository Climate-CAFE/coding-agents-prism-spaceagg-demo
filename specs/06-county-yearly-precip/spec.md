# Spec: Yearly county precipitation and map

## Approval

- **Status:** approved
- **Version:** draft 2, D9 amended (committed in d55de3b)
- **Last changed:** 2026-10-29 (D9 amended and approved)
- **Approved by:** project lead, via chat
- **Approved on:** 2026-10-28

## Goal

For each county and configured year, compute yearly total precipitation and mean daily precipitation from the Feature 5 county-day series, publish them only when every day is present, and draw one county choropleth of mean daily precipitation per year.

## Findings

- Feature 5 output: `data/output/prism_county_daily/2020/53/county_daily_2024.parquet`, 14,274 rows, units mm, all values present (coverage 1.0).
- Census county polygons are not in Feature 2 (blocks only). Dissolving Feature 2 blocks by `county_geoid` gives the county geometry without a new download.
- matplotlib 3.11.2 is already installed in `prism-spaceagg`. No new package is needed.

## Scope

**In scope**
- Yearly county Parquet per configured year, with the required columns.
- Essential completeness and value QC.
- County geometry from dissolved blocks, in memory.
- One PNG choropleth per year.
- Snakemake rule with incremental inputs on Feature 5 outputs.

**Out of scope**
- Reopening PRISM rasters, rebuilding the crosswalk, or changing Features 1–5.
- Gap filling, partial years, or annual aggregation other than total and mean.
- Multi-year or multi-state maps.
- Shapefile or GeoPackage output of county geometry.

## Key decisions

| ID | Decision |
|----|----------|
| D1 | Input: the Feature 5 daily county Parquet for the year. Read as one table (about 14k rows). |
| D2 | Complete record required: every county must have a non-null `precip_mm` on every expected date. Any missing daily county observation fails the run for the entire year; nothing is published (no partial or incomplete yearly results). |
| D3 | `precip_total_mm` = sum of the daily county means (mm). `precip_mean_mm` = `precip_total_mm / days_expected`, equal to the average of the daily means (mm/day). |
| D4 | `population` = the county's original Census population total (Feature 5 `population_total`), constant across the year. `population_year` (the Census reference year, from the vintage) is recorded in the output metadata. |
| D5 | Output columns: `county_geoid`, `year`, `population`, `days_observed`, `days_expected`, `precip_total_mm`, `precip_mean_mm`. `days_observed` counts non-null daily values; `days_expected` is the count of expected dates. |
| D6 | Output: one Parquet per year at `data/output/prism_county_yearly/{vintage}/{state_fips}/county_yearly_{year}.parquet`, written atomically after QC passes. Units, day definition, and `population_year` recorded in the Parquet metadata. |
| D7 | Essential QC (failure stops publication): row count equals the county count; `days_observed == days_expected` for every county; totals and means finite and ≥ 0; `precip_mean_mm × days_expected` equals `precip_total_mm` within 1e-9; population constant across days; the set of county GEOIDs in the yearly output equals the set of county GEOIDs in the Feature 2 Census blocks, with both missing counties (in blocks, absent from output) and unexpected counties (in output, absent from blocks) reported as failures. |
| D8 | County geometry: reuse county geometries from Feature 2 if available; they are not (Feature 2 holds blocks only), so dissolve Feature 2 blocks by `county_geoid` in EPSG:4269, in memory, with no additional download. Check: one valid polygon per county. |
| D9 | (Amended 2026-10-29, approved by project lead via chat.) Map: choropleth of `precip_mean_mm` (mm/day), one PNG per year at `data/output/figures/{vintage}/{state}/county_mean_daily_precip_{year}.png`. Title names the state, year, and variable. Drawn in the original Census CRS, EPSG:4269 (north-up, no reprojection), with the y-axis scaled by cos(mid-latitude) so the state keeps its true proportions. Colormap `LinearSegmentedColormap.from_list("blues_light", plt.cm.Blues(np.linspace(0.2, 1, 256)))`; normalization `PowerNorm(gamma=0.5, vmin=0, vmax=max of precip_mean_mm for the year)`. Thin gray county boundaries (`#555555`, 0.5 pt). Vertical colorbar labeled "mm/day". Detailed land geometry (coastline, Puget Sound, islands) from the original blocks, not simplified. Plotted with geopandas and matplotlib using the Agg backend. |
| D10 | Snakemake: rule per vintage, state, and year. Inputs: Feature 5 daily Parquet and QC JSON for the year, Feature 2 `blocks.parquet`, and config and code. Outputs: yearly Parquet, yearly QC JSON, PNG. Reruns only when inputs or recorded settings change. |
| D11 | Hydra: years from `prism.years`; vintage and state from `census`; paths from `datapaths.yaml` (`output_root`). Figures go in `{output_root}/figures`. |

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | Totals and means match a hand calculation on synthetic daily data. | Offline test. |
| AC2 | A county with a missing day fails the run and publishes no Parquet and no PNG. | Offline test. |
| AC3 | The PNG is written, has a title and colorbar label with units, and is non-empty. | Offline test (file exists, size > 0, image dimensions read back). |
| AC4 | Real 2024 run: 39 rows; `days_observed = days_expected = 366` for every county; `precip_mean_mm × 366 = precip_total_mm`. | Real run. |
| AC5 | Figure is viewable and the title, legend, and units are readable. | Visual inspection of the PNG. |
| AC6 | Features 1–5 inputs and outputs unchanged. | SHA-256 and mtime. |
| AC7 | Rerun plans nothing; a change to a setting or code plans only this rule. | `snakemake -n`. |
| AC8 | Paths and years come from Hydra; no hardcoded values in code. | Grep audit. |

## Open questions (resolved)

- [x] Q1: One Parquet per year (D6). Answered 2026-10-28.
- [x] Q2: Original Census population total, constant across the year; `population_year` in metadata (D4). Answered 2026-10-28.
- [x] Q3: County geometry from Feature 2 if available, else dissolved blocks with no download (D8). Answered 2026-10-28.
- [x] Q4: Any missing daily observation fails the whole year (D2). Answered 2026-10-28.
