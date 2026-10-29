# Tasks: Daily population-weighted county precipitation

Check a box only after its definition of done runs.

- [x] **T01 — Config and paths.** Serves: D10, D13. Files: `conf/datapaths.yaml` (`output_root`). DoD met: output path derived from Hydra config; years from `prism.years`; no new config file (per approval).
- [x] **T02 — Expected inputs and QC failure path.** Serves: D11, D15. DoD met: `require_validated_year` and `reference_grids` reused; failure writes the QC JSON with status `fail` and raises (verified by code path; no failure case in the real run).
- [x] **T03 — Window and reads.** Serves: D1, D2. DoD met: `cell_window` derives row and column from `cell_id`; `read_window` reads only that window from the ZIP; missing raster raises (test).
- [x] **T04 — Block means.** Serves: D3–D6. DoD met: NoData excluded, weights renormalized over valid cells, coverage reported; no valid cells gives NaN (tests).
- [x] **T05 — County means and QC.** Serves: D7–D9, D11. DoD met: population-weighted county means; `check_county_daily` checks values, duplicates, row count, dates, and county presence.
- [x] **T06 — Publish.** Serves: D10, D14. DoD met: Parquet written to `data/output/prism_county_daily/2020/53/county_daily_2024.parquet` with units and day definition in metadata; QC JSON written; atomic.
- [x] **T07 — Snakefile rule.** Serves: D12. DoD met: `aggregate_county_daily` with wildcards and content-hash params; dry run plans it when its output is missing.
- [x] **T08 — Tests.** Serves: AC1–AC3. DoD met: `pytest` 17 passed (14 existing + 3 new).
- [x] **T09 — Real run and checks.** Serves: AC4–AC8. DoD met: 14,274 rows (derived expected 366 × 39); values finite and ≥ 0; independent recomputation on three dates matches to 1e-15; Features 1–3 unchanged; rerun plans nothing.
