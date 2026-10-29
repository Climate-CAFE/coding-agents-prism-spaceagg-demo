# Status: Daily population-weighted county precipitation

- **Last updated:** 2026-10-28
- **Current phase:** complete (T01–T09 done)
- **Completed on:** 2026-10-28

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | approved | project lead, via chat | 2026-10-28 |
| plan.md | approved (change: no `conf/aggregation.yaml`) | project lead, via chat | 2026-10-28 |
| tasks.md | complete | — | — |

## Results (Washington 2024)

- Output: `data/output/prism_county_daily/2020/53/county_daily_2024.parquet`. 14,274 rows = 366 dates × 39 counties (derived at run time from the configured dates and the crosswalk's counties).
- QC: `data/metadata/prism_county_daily/2020/53/county_daily_2024_qc.json`, status `pass`. No duplicate county–date rows. Dates match the expected dates.
- Precipitation: all 14,274 values finite and ≥ 0. Range 0.0 to 87.03 mm.
- Population coverage: 1.0 for every row (minimum and mean). The Washington data contain no NoData cells inside the crosswalk window, so the NoData path is covered by synthetic tests only.
- Population: county totals sum to 7,705,281 on each date.
- Independent check: block and county means recomputed from full rasters on 2024-01-01, 2024-07-15, and 2024-12-31. Max difference 8.9e-16 across 39 counties.
- Metadata: Parquet schema records `units: mm` and the day definition (24 h ending 12:00 UTC; date is the PRISM file date).

## Blockers

None.

## Deviations

- `conf/aggregation.yaml` is not added (per approval). Units and day definition are constants in `src/county_precip.py`, written to the output metadata.
- Each run keeps the full `prism.years` list and selects its year with `+year=`. The Feature 4 grid check therefore still covers all years.
- Feature 4 was rebuilt once. Its params hash includes `src/qc.py`, so the Feature 5 edits to `qc.py` triggered it. The rebuilt crosswalk and QC are identical to the previous ones. This is an avoidable rebuild; it could be avoided by hashing only the Feature 4 section of `qc.py`. Not changed now.
- Feature 1–3 inputs and outputs are unchanged (mtime, size, inode).

## Validation results

| ID | Status | Evidence |
|----|--------|----------|
| AC1 | passing (test) | `test_block_and_county_means_match_hand_calculation` |
| AC2 | passing (test) | `test_nodata_cell_is_excluded_and_weights_renormalize` |
| AC3 | passing (test) | `test_county_without_valid_blocks_is_blank_and_missing_raster_raises` |
| AC4 | passing | 14,274 rows, no duplicates, dates and counties complete |
| AC5 | passing | 14,274 rows; all values finite and ≥ 0; coverage 1.0 |
| AC6 | passing | Features 1–3 inputs unchanged; crosswalk rebuild identical |
| AC7 | passing | dry run plans nothing; content change plans only the affected rules |
| AC8 | passing | paths and years from Hydra; constants limited to fixed conventions |

## Next steps

None. Feature 5 is complete.
