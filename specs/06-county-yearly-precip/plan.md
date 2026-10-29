# Plan: Yearly county precipitation and map

- **Spec:** `specs/06-county-yearly-precip/spec.md` (draft 1, approved 2026-10-28)
- **Status:** awaiting approval (gate 2)

## Approach

One Hydra-configured script handles one year. It reads the Feature 5 daily county Parquet, requires a complete record for every county, sums the daily county means, and divides by the expected days. It then runs QC, publishes the yearly Parquet atomically, and draws one PNG. County outlines come from dissolving Feature 2 blocks in memory.

## Layout

```
src/yearly_precip.py           # NEW: read daily, yearly sums and means, county outlines, publish, map
src/qc.py                      # ADD "Feature 6: yearly county precipitation" section
Snakefile                      # ADD yearly rule and targets (Features 1–5 unchanged)
tests/test_yearly_precip.py    # NEW: 3 synthetic tests
```

No new configuration file and no new packages (matplotlib 3.11.2 and geopandas are installed). Paths and years come from the existing Hydra config.

## Modules

1. **Input** — `read_daily(path)`: read the Feature 5 county-day Parquet for the year, with the expected dates from Feature 1 `expected_dates`.
2. **Complete record** — a county missing any expected date (null or absent) fails the year (D2). Failure writes the QC JSON with status `fail` and raises; no outputs are published.
3. **Yearly values** — per county: `precip_total_mm` = sum of daily `precip_mm` (D3); `precip_mean_mm` = total ÷ `days_expected` (D3); `population` = the constant Census `population_total` (D4); `days_observed` = non-null daily values; `days_expected` = count of expected dates (D5).
4. **Outlines** — `county_outlines(blocks)`: read Feature 2 `blocks.parquet` (block geometry and `county_geoid`), `dissolve(by="county_geoid")` in EPSG:4269 (D8). Check one valid polygon per county.
5. **QC** — `src/qc.py` Feature 6 section, essential only: row count equals the county count; `days_observed == days_expected` for every county; totals and means finite and ≥ 0; `precip_mean_mm × days_expected` equals `precip_total_mm` within 1e-9; population constant across days; county GEOIDs in the output equal the Feature 2 block county GEOIDs, reporting missing and unexpected counties separately; one valid outline per county.
6. **Publish** — Parquet with columns `county_geoid`, `year`, `population`, `days_observed`, `days_expected`, `precip_total_mm`, `precip_mean_mm`; metadata keys `units` (`precip_total_mm` mm; `precip_mean_mm` mm/day), `population_year` (the Census vintage), and the day definition inherited from Feature 5. Written as `.tmp` then renamed.
7. **Map** — `draw_map(outlines, yearly, path, state, year)`: choropleth of `precip_mean_mm` using geopandas `plot` with matplotlib (Agg backend). Title: state name, year, and "mean daily precipitation"; colorbar label "mean daily precipitation (mm/day)". Written to `{output_root}/figures/county_mean_daily_precip_{year}.png`. Figure produced only after QC passes.
8. **Workflow** — `Snakefile`: rule `yearly_county_precip` with wildcards `vintage`, `state_fips`, `year`. Inputs: Feature 5 daily Parquet and QC JSON for the year, Feature 2 `blocks.parquet`, config and code files. Outputs: yearly Parquet, yearly QC JSON, PNG. Params: content hashes of `src/yearly_precip.py`, `src/qc.py`, `conf/census.yaml`, `conf/prism_ppt.yaml`, so content changes rebuild this rule only. Each run keeps the full `prism.years` list and selects its year with `+year=`, as in Feature 5.
9. **Tests** — `tests/test_yearly_precip.py`, three synthetic tests:
   - totals and means match a hand calculation (two counties, four days);
   - a missing day in one county raises and nothing is published;
   - the map writes a non-empty PNG for a two-county synthetic outline set.

## Skills applied

- **python-pipeline-style:** Hydra entry point, `pathlib`, logging, QC in `qc.py`, pytest.
- **snakemake-workflow:** wildcard rule, declared outputs, content-hash params.
- **dataviz:** read before writing the map code, as its trigger requires for any chart. The map stays a single titled choropleth with a labeled colorbar and a sequential palette.

## Configuration

| Parameter | Value | File | Decision |
|-----------|-------|------|----------|
| Years | from `prism.years` | `prism_ppt.yaml` | D11 |
| Vintage, state | 2020, `"53"` | `census.yaml` | D4, D11 |
| Output root | `data/output` | `datapaths.yaml` | D6, D11 |
| Figure folder | `{output_root}/figures` | derived | D9 |
| Population reference year | from the vintage (2020) | `census.yaml` | D4 |

## Data manifest

| Dataset | Version | Location | Transformations | Stage |
|---------|---------|----------|-----------------|-------|
| County daily precipitation | Feature 5, 2024 | `data/output/prism_county_daily/2020/53/county_daily_2024.parquet` | Read only | yearly |
| Census blocks | Feature 2, 2020 | `data/intermediate/census/2020/53/blocks.parquet` | Dissolved by county | outlines |
| Yearly county precipitation | per run | `data/output/prism_county_yearly/2020/53/county_yearly_2024.parquet` | Sums and means | output |
| Choropleth | per run | `data/output/figures/county_mean_daily_precip_2024.png` | None | figure |
| QC report | per run | `data/metadata/prism_county_yearly/2020/53/county_yearly_2024_qc.json` | None | QC |

## Traceability

| Spec item | Element | Task |
|-----------|---------|------|
| D1 | `read_daily` | T02 |
| D2 | complete-record check and failure path | T03 |
| D3 | yearly sums and means | T03 |
| D4 | population and `population_year` metadata | T03, T05 |
| D5 | output columns | T03 |
| D6 | publish step | T05 |
| D7 | `check_yearly` in `qc.py` | T04 |
| D8 | `county_outlines` | T02 |
| D9 | `draw_map` | T06 |
| D10 | `Snakefile` rule | T07 |
| D11 | Hydra config and paths | T01 |
| AC1 | totals and means test | T08 |
| AC2 | missing-day test | T08 |
| AC3 | PNG test | T08 |
| AC4 | real 2024 run | T09 |
| AC5 | visual check of the PNG | T09 |
| AC6 | checksums and mtimes | T09 |
| AC7 | `snakemake -n` after changes | T09 |
| AC8 | config audit | T09 |

## Validation

- **Tests:** `pytest` in `prism-spaceagg`, including the 17 existing tests.
- **Real run:** 2024. Expect 39 rows, `days_observed = days_expected = 366` for every county, `precip_mean_mm × 366 = precip_total_mm` within tolerance. Spot-check three counties against Feature 5 daily values.
- **Figure:** open the PNG and confirm title, colorbar label, and units.
- **Originals:** Features 1–5 SHA-256 and mtimes unchanged.
- **Incremental:** rerun plans nothing; a settings or code change plans only `yearly_county_precip`.

## Risks

| Risk | Mitigation |
|------|------------|
| Dissolving 158k blocks is slow | Dissolve once per run; dissolve only the needed columns. |
| Block union leaves slivers or invalid outlines | Check validity; fail the run if any county outline is invalid. |
| A single-year map has little visual contrast | Fixed colorbar limits are not used; the colorbar shows the actual range. |

## Alternatives considered

- One combined multi-year Parquet: rejected by your decision (D6).
- Downloading the national county file: rejected by your decision (D8).
- Partial years: rejected by your decision (D2).
