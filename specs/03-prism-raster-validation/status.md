# Status: PRISM raster inspection and validation

- **Last updated:** 2026-10-28
- **Current phase:** complete (T01–T08 done)
- **Completed on:** 2026-10-28

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | approved | project lead, via chat | 2026-10-28 |
| plan.md | approved | project lead, via chat | 2026-10-28 |
| tasks.md | complete | — | — |
| `rasterio` 1.5.2 install | installed | project lead, via chat | 2026-10-28 |

## Results

- Format: each ZIP holds a GeoTIFF (`.tif`) with sidecars, not BIL. Read in place via `/vsizip/`.
- Output: `data/metadata/prism/ppt/2024/raster_validation.csv`, 366 rows, one per date.
- Reference: 2024-01-01. CRS EPSG:4269, 7025 × 3105 cells, NoData -9999.0.
- Validation: 366 TRUE, 0 with issues.
- Originals: ZIP SHA-256 matches Feature 1's manifest for all 366. Mtime, size, and inode unchanged.
- Incremental: `snakemake -n` reports nothing to be done.

## Blockers

None.

## Deviations

- None from the approved spec and plan.
- Feature 1's `.snakemake` provenance warning for `download_prism_ppt` is unchanged from before (left as is by decision).

## Validation results

| ID | Status | Evidence |
|----|--------|----------|
| AC1 | passing | 366 rows; `test_matching_grid_gives_true_for_every_date`, real run |
| AC2 | passing | reference is 2024-01-01; `test_each_problem_gets_its_issue_code` |
| AC3 | passing | `test_each_problem_gets_its_issue_code` covers missing, unreadable, shape, NoData (mismatch and missing), transform |
| AC4 | passing | `test_rotated_reference_makes_every_row_invalid` |
| AC5 | passing | real 2024 run: 366 readable, all TRUE, no issues |
| AC6 | passing | SHA-256 matches Feature 1 manifest for 366/366; mtime, size, inode unchanged |
| AC7 | passing | `snakemake -n`: nothing to be done |
| AC8 | passing | audit of new code finds no hardcoded values |

## Next steps

None. Feature 3 is complete.
