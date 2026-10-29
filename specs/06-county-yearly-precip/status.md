# Status: Yearly county precipitation and map

- **Last updated:** 2026-10-28
- **Current phase:** complete (T01–T09 done)
- **Completed on:** 2026-10-28

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | approved | project lead, via chat | 2026-10-28 |
| plan.md | approved | project lead, via chat | 2026-10-28 |
| tasks.md | complete | — | — |

## Results (Washington 2024)

- Yearly output: `data/output/prism_county_yearly/2020/53/county_yearly_2024.parquet`. 39 rows, one per county, with `population_year = 2020` in metadata.
- Completeness: `days_observed = days_expected = 366` for every county.
- Totals and means: `precip_mean_mm × 366 = precip_total_mm` (max difference 2.3e-13). Totals equal the sum of Feature 5 daily county means (difference 0.0).
- Population: 7,705,281 total; constant per county across the year.
- Precipitation: totals 199.6–2,208.2 mm; means 0.55–6.03 mm/day.
- County set: equals the Feature 2 block county set, with no missing and no unexpected counties.
- Map: `data/output/figures/2020/53/county_mean_daily_precip_2024.png`. Title and subtitle in one block, vertical mm/day colorbar, Blues colormap with PowerNorm(gamma=0.5), EPSG:4269 north-up, pure white background, viewed (2026-10-29 visualization update).
- QC: `data/metadata/prism_county_yearly/2020/53/county_yearly_2024_qc.json`, status `pass`.
- Tests: 20 pass.
- Rerun: `snakemake -n` plans nothing.
- Snakemake run 2026-10-29: after the code-hash change, `snakemake` planned only `yearly_county_precip` for 2024 and rebuilt it; Parquet and QC checksums unchanged; PNG regenerated. Log: `logs/yearly_county_precip_2020_53_2024.log`.

## Blockers

None.

## Deviations

- Figure path: `data/output/figures/{vintage}/{state}/county_mean_daily_precip_{year}.png`, not `data/output/figures/county_mean_daily_precip_{year}.png` as approved. Snakemake requires all outputs of a rule to share the same wildcards.
- Snakemake params now hash only the QC sections each rule uses (shared helpers plus the features it imports), not the whole `src/qc.py`. Features 4 and 5 were rebuilt once for this change and for the `state_name` addition in `conf/census.yaml`. Their outputs are identical to the previous ones.
- `src/qc.py` is no longer listed as an mtime input of Features 4–6. The content hashes cover it.
- Feature 5 was not rebuilt by the approved change path; it was rebuilt because its upstream Feature 4 output was rewritten. Its output is identical.
- D9 amended on 2026-10-28 at the project lead's request, in chat: map drawn in EPSG:4269 (was EPSG:5070 for display), `PowerNorm` and the Blues-based colormap, `#555555` 0.5 pt county boundaries, colorbar label "mm/day" (was "mean daily precipitation (mm/day)"), and a cos(mid-latitude) y-axis scale so the state keeps its true proportions. Those changes were not in the approved spec. The project lead approved the amended D9 via chat on 2026-10-29, and `spec.md` records it.
- Visualization-only change on 2026-10-29: pure white background (was `#fcfcfb`), constrained layout, title and subtitle combined into one `set_title` block. Parquet and QC checksums unchanged across all regenerations.

## Validation results

| ID | Status | Evidence |
|----|--------|----------|
| AC1 | passing (test) | `test_totals_are_sums_and_means_are_totals_over_expected_days` |
| AC2 | passing (test) | `test_missing_day_or_unexpected_county_fails_the_year` (no outputs written on failure path) |
| AC3 | passing (test) | `test_map_writes_a_titled_png` |
| AC4 | passing | 39 rows; 366 days observed for every county; means × 366 = totals |
| AC5 | passing | PNG viewed: title, legend with mm/day, Washington's counties |
| AC6 | passing | Features 1–3 inputs and outputs unchanged; Features 4–5 rebuilt identical |
| AC7 | passing | dry run plans nothing |
| AC8 | passing | paths and years from Hydra; state name in `census.yaml` |

## Next steps

None. Feature 6 is complete.
