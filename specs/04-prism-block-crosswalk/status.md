# Status: PRISM fishnet, Census block–cell crosswalk, and area weights

- **Last updated:** 2026-10-28
- **Current phase:** complete (T01–T10 done)
- **Completed on:** 2026-10-28

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | approved | project lead, via chat | 2026-10-28 |
| plan.md | approved | project lead, via chat | 2026-10-28 |
| tasks.md | complete | — | — |

## Results (Washington 2020)

- Fishnet: 401,940 cells (reported, not compared to a benchmark). IDs unique; `cell_id = row * 7025 + col + 1` checked on 5 sampled cells.
- Crosswalk: 816,566 rows. Unique (block, cell) pairs. Weights sum to 1 per block (max error 2.2e-16). Population from crosswalk blocks: 7,705,281, matching the Census total.
- Coverage: 3 blocks below 0.99 (warnings, run passes):
  - 530330093001008 (0.9898)
  - 530630123003003 (0.9865)
  - 530439603002172 (0.0, population 0, no crosswalk rows)
- Slivers: 2,443 overlaps ≤ 10 m² removed, 8,264.6 m² in total.
- Outputs: `data/intermediate/crosswalk/2020/53/fishnet.parquet` (GeoParquet), `block_cell_crosswalk.parquet` (Parquet), and `data/metadata/crosswalk/2020/53/qc_report.json`.
- Rebuilt once after recording rule params; output and QC match the earlier run exactly.

## Blockers

None.

## Deviations

- Low-coverage count is 3. The third block has population 0 and no crosswalk rows. Reported as-is; the run passes.
- Snakemake does not trigger a rebuild on a timestamp-only change (`touch`) to a config file. Content changes do. The rule now records config and code content hashes as params (`src/crosswalk.py`, `src/qc.py`, `conf/census.yaml`, `conf/prism_ppt.yaml`, `conf/crosswalk.yaml`). This is a change from the approved plan, which assumed timestamps would work.
- Feature 1–3 rules are unchanged. Their inputs and outputs were not modified.
- Feature 1's `.snakemake` provenance warning is unchanged (left as is by decision).

## Validation results

| ID | Status | Evidence |
|----|--------|----------|
| AC1 | passing | IDs unique; formula spot-checked on the raster |
| AC2 | passing | unique (block, cell) pairs |
| AC3 | passing | max |sum−1| = 2.2e-16 |
| AC4 | passing | 7,705,281 |
| AC5 | passing (test) | `test_populated_block_without_cells_fails_the_check` |
| AC6 | passing | 3 blocks warned; run passes |
| AC7 | passing | 401,940 cells reported; no benchmark comparison |
| AC8 | passing | Feature 1–3 inputs and outputs unchanged |
| AC9 | passing | rerun plans nothing; content change plans only `build_crosswalk` |
| AC10 | passing | parameters in `conf/crosswalk.yaml` |

## Next steps

None. Feature 4 is complete.
