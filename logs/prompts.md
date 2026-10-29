
## Prompt

````text
We are starting a new project to build a reproducible, modular Python pipeline for daily population-weighted PRISM 800m precipitation estimates for U.S. counties using Census block boundaries and population data, with annual county-level summaries. Use Washington State and 2024 as the initial example, but design for configurable dates, multiple years, and other states. Develop one feature at a time. For Feature 1, download daily PRISM precipitation (ppt) for the full year 2024 from https://data.prism.oregonstate.edu/time_series/us/an/800m/. Use Hydra/YAML for configuration, Snakemake for orchestration, and save original ZIPs under data/raw/prism/ppt/<year>/. Support incremental downloads, file validation, and failure handling. Follow AGENTS.md, CLAUDE.md, and relevant Skills and create specs/01-prism-download/spec.md using create-specs. Keep the implementation minimal and present the plan for approval before writing code or downloading data.
````

---

## Prompt

````text
I approve D1–D8 with a few changes. Keep original ZIPs under data/raw/ and store manifests under data/metadata/prism/ppt/<year>/. Support configurable years and date ranges, with 2024 as the initial run. Use three retry attempts, a 0.5-second pause, and record checksums and source stability when available. I approve the ~2.8 GB download after implementation review.

Please simplify the specification significantly. Keep it short and focused on the goal, scope, key decisions, acceptance criteria, and unresolved questions. Avoid lengthy explanations, repetitive sections, and unnecessary documentation. Apply this concise format to future feature specifications as well.

Update .gitignore to exclude downloaded data and generated logs, but keep logs/prompts.md tracked. Update the spec and proceed with plan.md for approval. 
````

---

## Prompt

````text
I approve plan.md with a few structural changes: keep a single Snakefile at the repository root, use src/download_prism.py for downloading and manifest generation, and add src/qc.py for reusable QC checks and reporting. Centralize all data paths in conf/datapaths.yaml, keep PRISM-specific settings in conf/prism_ppt.yaml, and use conf/config.yaml for Hydra composition. Do not modify the create-specs Skill or its templates; just keep future specifications concise while retaining the required sections. For PRISM stability, record not available unless an official source confirms otherwise. Update the plan accordingly and proceed with tasks.md .
````

---

## Prompt

````text
I approve creating the prism-spaceagg Conda environment. Proceed with implementation tasks T01–T09, following the approved spec and plan.
````

---

## Prompt

````text
Let's simplify Feature 1 further. Keep src/download_prism.py focused on downloading, retries, incremental reruns, and manifest generation. Move all validation and QC logic into src/qc.py, organized into feature-specific sections so future features can add their QC functions there. The downloader can call validation functions from qc.py as needed. Keep only one test file, tests/test_download_prism.py, covering essential download and QC behavior; remove tests/test_qc.py and avoid excessive testing or abstractions. Retain the single root Snakefile, Hydra configuration, and original ZIP files.
````

---

## Prompt

````text
I approve the updated Feature 1 implementation and T10, including the ~2.8 GB PRISM 2024 download. The simplified structure and five tests are sufficient for now; no additional tests or modules are needed. Please proceed with the download, validate that all 366 ZIP files pass QC, verify the manifest and checksums, and perform a second run to confirm that valid files are skipped without being modified. Report the results and any failures concisely.
````

---

## Prompt

````text
Let's start Feature 2: Census Blocks and Population Download. Download the official 2020 TIGER/Line Census block shapefile (`TABBLOCK20`) for Washington State (FIPS `"53"`), using its existing `POP20` field. Keep Census vintage, state FIPS, source URL, and expected CRS configurable through Hydra (`conf/census.yaml`) to support other states and vintages without code changes. Preserve the original ZIP under `data/raw/census/{vintage}/{state_fips}/` and create a cleaned GeoParquet under `data/intermediate/census/{vintage}/{state_fips}/blocks.parquet`, containing `state_fips`, `county_geoid`, `block_geoid`, `population`, `geometry`, and `vintage`. Define base paths in `conf/datapaths.yaml` and derive paths dynamically. Add `src/census_blocks.py`, reuse Feature 1 download utilities where practical, extend the existing `src/qc.py` with a small Feature 2 section, and update the root `Snakefile`. Keep QC simple: check required columns, unique block GEOIDs, nonmissing and nonnegative population, valid geometries, CRS, and population and county totals. Make reference totals configurable by vintage and state; initially use Washington's population (7,705,281) and 39 counties. If reference values are unavailable, skip those comparisons with a warning. Write a concise QC JSON report and publish GeoParquet only when essential checks pass. Add only a few focused offline tests for successful processing and critical failures; avoid excessive edge-case tests, additional QC modules, or unnecessary abstractions. Ensure incremental Snakemake execution without affecting Feature 1. Follow `AGENTS.md`, `CLAUDE.md`, and applicable Skills. Use `create-specs` to draft a concise specification for approval before planning or coding. Do not modify the `create-specs` Skill or its templates.
````

---

## Prompt

````text
I approve the Feature 2 specification and all four points: (1) Use EPSG:4269 as the expected CRS and verify it against the downloaded file. (2) You may add geopandas, pyogrio, and pyarrow to `environment.yaml` and install them in `prism-spaceagg`. (3) You have approval to download the ~204 MB Census ZIP. (4) Reuse Feature 1's `fetch_file` and related utilities through a compatible Census configuration without modifying Feature 1. Please proceed with the implementation plan and stop at the next approval gate before coding. Keep the implementation, QC, and tests minimal and avoid overengineering.
````

---

## Prompt

````text
I approve the Feature 2 implementation plan and both decisions. Use Snakemake wildcards for Census vintage and state FIPS, with targets configured in conf/census.yaml. Add Census to the existing Hydra defaults in conf/config.yaml; no separate configuration root is needed. Please proceed with tasks.md and implementation, including the approved package installation and Census download. Keep the code, QC, and three offline tests minimal, reuse existing utilities, and leave Feature 1 unchanged.
````

---

## Prompt

````text
Thanks, Feature 2 looks good. Let's leave the PRISM provenance metadata as it is for now; don't run `snakemake --touch` or modify Feature 1 outputs. Please ensure the Feature 2 status is marked complete and all verification results are documented. No further changes are needed for this feature.
````
---

## Prompt

````text
Let's start Feature 3: PRISM Raster Inspection and Validation. Validate the daily PRISM precipitation rasters downloaded in Feature 1. First inspect the actual ZIP contents to identify the raster format and supporting files rather than assuming BIL or GeoTIFF. Read the rasters directly from their ZIP archives using Rasterio/GDAL where supported, without permanently extracting or modifying the original files. Reuse the existing raster-processing Skill utilities for metadata inspection and grid alignment checks, avoiding duplicated logic. Add src/validate_rasters.py for orchestration and extend src/qc.py with a small Feature 3 section. Use the first configured date as the reference raster, not the first readable date. Validate CRS, dimensions, resolution, bounds, affine transform, and NoData across configured dates. Report missing files, unreadable rasters, invalid reference metadata, rotated transforms, and grid mismatches. Add prism.transform_tol: 1.0e-9 to the Hydra configuration for affine transform comparisons, requiring exact CRS and dimension matches. Generate raster_validation.csv under the configured metadata directory, with one row per date, issue codes, and a matches_reference field (TRUE, FALSE, or blank when comparison is impossible). Extend the existing root Snakefile with an incremental validation rule that depends on Feature 1 outputs without unnecessarily rerunning downloads or Census processing. Add only a few focused offline tests. Keep the implementation minimal, modular, and reusable across configured years and date ranges. Do not resample, reproject, or modify the original rasters. Follow AGENTS.md, CLAUDE.md, and applicable Skills. 
````

---

## Prompt

````text
I approve the Feature 3 specification with these decisions: (1) You may install rasterio from conda-forge into prism-spaceagg and add it to environment.yaml. (2) Reuse the raster-processing Skill's inspect_raster and validate_same_grid functions by importing them from their existing path rather than copying code. (3) Keep validation report-only (exit 0), recording all issues in the CSV without failing the workflow for raster metadata mismatches. (4) Read the actual NoData value from the first configured raster and use it as the reference for subsequent dates, reporting missing or inconsistent values. Please proceed with the concise implementation plan and stop at the next approval gate before coding. Keep QC and tests minimal.
````

---

## Prompt

````text
I approve both decisions and the Feature 3 implementation plan. Keep the proposed NoData validation logic and the three focused tests. Please proceed with implementation, including the approved Rasterio installation. Run the tests and Snakemake workflow, inspect the resulting validation CSV, and update `status.md` with the results. Keep the implementation minimal, avoid overengineering QC or tests, and leave Features 1 and 2 unchanged.
````

---

## Prompt

````text
Let's start Feature 4: PRISM Fishnet, Census Block Intersections, and Area Weights. Use the validated PRISM grid from Feature 3 and Census blocks from Feature 2 to generate a reusable fishnet and block-to-cell spatial crosswalk for the configured state. Generate only the raster window covering the state with a configurable 2-cell margin, and preserve full-grid cell IDs using cell_id = row * raster_width + col + 1. Reuse the existing raster-processing and areal-overlay Skills rather than duplicating their utilities. Intersect Census blocks with PRISM cells, densify polygon edges by 0.0001° before projecting to EPSG:5070 for area calculations, exclude overlaps ≤10 m², and calculate each intersection's area weight relative to its block's total retained intersection area. Include block GEOID, county GEOID, cell ID, population, overlap area, area weight, and block coverage in the crosswalk. Configure fishnet_margin_cells: 2, densify_deg: 0.0001, area_crs: EPSG:5070, min_overlap_m2: 10, weight_tol: 1.0e-9, and low_coverage_threshold: 0.99 through Hydra. Save the fishnet and crosswalk as GeoParquet or Parquet under data/intermediate/, with paths configurable by state and Census vintage. Add src/crosswalk.py, extend the existing src/qc.py and root Snakefile, and keep QC focused on unique cell IDs, unique block-cell pairs, weights summing to 1, population consistency, and missing populated blocks. Report low coverage as a warning rather than a failure. Use the previous Washington results as reference benchmarks where applicable: approximately 401,940 fishnet cells, 7,705,281 total population, and two blocks below 99% coverage. Add only a few focused synthetic tests; avoid extensive edge-case testing or unnecessary modules. Do not modify Features 1–3 or the original input data. Follow AGENTS.md, CLAUDE.md, and applicable Skills.
````

---

## Prompt

````text
I approve the Feature 4 specification with the following decisions: Densify both Census block and PRISM cell edges by 0.0001° before projecting to EPSG:5070. Keep the original block population in each crosswalk row rather than an allocated population value, since population allocation will happen during aggregation in Feature 5. Do not install Fiona; instead, reuse the small cell_polygon() logic from the raster-processing Skill locally in src/crosswalk.py using Rasterio and Shapely, without modifying the original Skill. Save the fishnet as GeoParquet and the crosswalk as regular Parquet without unnecessary intersection geometries. Use the first configured PRISM year's validated reference grid to generate the reusable fishnet and crosswalk, and reuse them across years only when their raster grids have been validated as identical. Please proceed with the concise Feature 4 implementation plan and stop at the next approval gate before coding. Follow the existing Hydra and Snakemake conventions, keep QC and synthetic tests minimal, avoid unnecessary dependencies or overengineering.

````

---

## Prompt

````text

I approve the Feature 4 implementation plan. The cross-year approach is fine: build the fishnet and crosswalk once using the first configured year's validated reference grid, and reuse them for other years only after confirming identical grids. The Snakemake dependencies on the reference year's raster validation CSV and Census blocks are appropriate; also ensure relevant configuration and code changes trigger rebuilding when necessary, without unnecessarily rerunning Features 1–3. 
````

---

## Prompt

````text
Let's start Feature 5: Daily Population-Weighted County Precipitation Aggregation. Using the validated daily PRISM GeoTIFFs from Feature 3 and the Census block–cell crosswalk from Feature 4, calculate population-weighted daily precipitation for each county in the configured state and year. Read the GeoTIFFs directly from their original ZIP archives without extracting or modifying them. For each day, use the crosswalk's cell_id to derive raster row and column positions from the full raster width, extract precipitation values, and calculate each block's precipitation as the area-weighted average of its intersecting PRISM cells. Then aggregate to county level using the original Census block populations as weights. Handle PRISM NoData values explicitly: exclude missing raster values and renormalize valid cell weights within each block, while reporting missing-data coverage rather than silently treating NoData as zero. Save daily county-level results as Parquet, including county_geoid, date, population-weighted precipitation in millimeters, and relevant population coverage information. Keep the implementation modular and efficient by reusing the existing crosswalk and processing one date at a time rather than loading all 366 rasters into memory. Use Hydra for configurable years, paths, and settings, and extend the existing root Snakefile with incremental dependencies on the Feature 4 crosswalk and Feature 3 validation outputs. Extend src/qc.py with only essential checks for valid precipitation values, county coverage, duplicate county-date records, and expected dates. Add a few focused synthetic tests, avoiding extensive QC or overengineering. 
````

---

## Prompt

````text
I approve the Feature 5 specification with these decisions: Use millimeters for daily precipitation (precip_mm), based on PRISM's documented units, and note that the units are not explicitly recorded in the raster metadata. Preserve the original PRISM date for each observation and document the 24-hour period ending at 12:00 UTC without applying any local-day shift. Save validated county-level daily precipitation outputs under data/output/, following the existing Hydra path conventions. Treat missing or unreadable required rasters as failures rather than silently skipping dates or publishing incomplete results. For Washington in 2024, 14,274 county-date rows is a useful reference count, but do not hardcode it; derive the expected count from the configured dates and counties.
````

---

## Prompt

````text
I approve the Feature 5 implementation plan with one simplification: do not add conf/aggregation.yaml solely for the precipitation units and PRISM day definition, since these are fixed dataset conventions already documented in AGENTS.md. Record them in the output metadata instead. The proposed output path data/output/prism_county_daily/{vintage}/{state}/county_daily_{year}.parquet is approved. Keep the existing Hydra configuration for paths, years, and other relevant settings. Proceed with the one-year-at-a-time aggregation, reading only the required raster window, applying the approved population-weighted calculations and NoData handling, and publishing outputs atomically after QC passes. Keep the three focused synthetic tests, run the full existing test suite and Snakemake workflow, and verify the actual county-date counts, population coverage, and precipitation results. Do not hardcode the Washington reference count. 
````

---

## Prompt

````text
Let's start Feature 6: Yearly County Precipitation Aggregation and Visualization. Using the daily population-weighted county precipitation Parquet outputs from Feature 5, calculate yearly total precipitation (precip_total_mm) as the sum of daily county means and yearly mean daily precipitation (precip_mean_mm) as their average, for each county and configured year. Preserve county_geoid, year, population, days_observed, and days_expected, and require complete daily records before publishing yearly results. Save the yearly results as Parquet under data/output/prism_county_yearly/{vintage}/{state}/. Also generate one simple county-level choropleth map per year showing yearly mean daily precipitation in mm/day, using the county geometries available from Feature 2 or deriving them from Census blocks if necessary. Save the figure as PNG under data/output/figures/, with a clear title, legend, and units. Keep the visualization minimal and avoid unnecessary plotting dependencies. Add src/yearly_precip.py, extend the existing src/qc.py with essential yearly completeness and value checks, and update the root Snakefile with incremental dependencies on the Feature 5 daily outputs. Use the existing Hydra configuration and processing conventions, add only a few focused synthetic tests, and avoid unnecessary modules or overengineering. Do not reopen PRISM rasters, rebuild the crosswalk, or modify Features 1–5 or existing Skills.
````

---

## Prompt

````text
I approve the Feature 6 specification with these decisions: Use one yearly Parquet file per year, consistent with Feature 5, rather than combining multiple years into one file. Keep the original Census county population total, constant across the year, and record the population reference year as population_year in the output metadata. For the choropleth map, reuse county geometries from Feature 2 if available; otherwise derive them by dissolving Census blocks by county_geoid, without downloading additional data. Treat any missing daily county observation as a failure for the entire year, and do not publish incomplete yearly results. Keep the yearly total as the sum of daily population-weighted county means and the yearly mean as that total divided by the expected number of days.
````

---

## Prompt

````text
One additional QC clarification for Feature 6: Please verify that the set of county GEOIDs in the yearly output exactly matches the set of counties in the Feature 2 Census blocks, checking for both missing and unexpected counties.
````

---

## Prompt

````text
approve the Feature 6 plan
````

---


## Prompt

````text
Please improve the Feature 6 choropleth visualization. The current map has overly simplified county boundaries, a large amount of whitespace, and a horizontal color bar positioned too far below the map. I want a more detailed, publication-quality Washington State map that preserves the coastline, Puget Sound, islands, inland water boundaries, and county outlines. Use the original Census block geometries to derive detailed county boundaries without unnecessary simplification or downloading new data. Make the map larger and centered, with minimal whitespace, thin gray county boundaries, and a vertical blue color bar on the right labeled "mm/day". Use the main title "Mean Daily Population-Weighted Precipitation (mm/day)" and subtitle "Washington State | 2024". Keep the existing yearly precipitation values, color scheme, aggregation logic, Parquet outputs, and QC unchanged. Modify only the visualization code and regenerate the PNG. Avoid unnecessary dependencies or additional figures.

````

---

## Prompt

````text
Please update Feature 6. Plot county geometries in their original Census CRS (EPSG:4269) rather than EPSG:5070, so Washington appears in its familiar north-up orientation. Use a customized Matplotlib Blues colormap defined by LinearSegmentedColormap.from_list("blues_light", plt.cm.Blues(np.linspace(0.2, 1, 256))) and PowerNorm(gamma=0.5, vmin=0, vmax=vmax) for color normalization. Use thin gray county boundaries (edgecolor="#555555", linewidth=0.5), a vertical color bar labeled "mm/day", and a compact layout with minimal whitespace. Preserve the detailed coastline, Puget Sound, and islands; avoid unnecessary geometry simplification. Keep the existing yearly precipitation values, aggregation logic, Parquet outputs, and QC unchanged. Modify only the visualization code and regenerate the PNG.
````
---
