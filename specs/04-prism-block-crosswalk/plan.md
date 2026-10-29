# Plan: PRISM fishnet, Census block–cell crosswalk, and area weights

- **Spec:** `specs/04-prism-block-crosswalk/spec.md` (draft 1, approved 2026-10-28)
- **Status:** approved 2026-10-28, via chat (change: no fishnet-size comparison; report the actual count only)

## Approach

One script reads the reference PRISM grid (first configured date of the first configured year, via Feature 3's `inspect_raster`), builds the window fishnet, densifies blocks and cells, projects to EPSG:5070, intersects, removes slivers, computes weights and coverage, runs QC, and publishes the two outputs only if essential checks pass. Each cell's polygon comes from a local copy of the Skill's `cell_polygon()`.

## Layout

```
conf/crosswalk.yaml             # NEW: fishnet_margin_cells, densify_deg, area_crs, min_overlap_m2, weight_tol, low_coverage_threshold
conf/config.yaml                # ADD crosswalk to defaults
src/crosswalk.py                # NEW: reference grid, window, fishnet, crosswalk, publish
src/qc.py                       # ADD "Feature 4: block–cell crosswalk" section
Snakefile                       # ADD build_crosswalk rule and targets (Features 1–3 unchanged)
tests/test_crosswalk.py         # NEW: 3 synthetic tests
```

No new packages: geopandas, pyproj (through geopandas), shapely, rasterio, and pyarrow are already installed.

## Modules

1. **Config** — `conf/crosswalk.yaml` with the six parameters. State and vintage come from `conf/census.yaml`; PRISM settings from `conf/prism_ppt.yaml`.
2. **Reference grid** — `crosswalk.reference_grid(cfg)`: first expected PRISM date of `prism.years[0]`, read with Feature 3's `inspect_raster` (imported by path, as in Feature 3). Requires that year's `raster_validation.csv` with no issues.
3. **Window** — `crosswalk.window(blocks_bounds, transform, width, height, margin)`: convert the block bounding box to rows and columns, expand by the margin, clip to the raster.
4. **Fishnet** — `crosswalk.cell_polygon(transform, row, col)` (local copy of the Skill's function) and `build_fishnet`: one polygon per window cell, `cell_id = row * width + col + 1`, GeoParquet in EPSG:4269.
5. **Crosswalk** — `build_crosswalk(blocks, fishnet, cfg)`:
   - densify both sets (`segmentize` by `densify_deg`) in EPSG:4269;
   - project to `area_crs`;
   - sjoin on bounding boxes, then intersect;
   - drop overlaps ≤ `min_overlap_m2` and record the count and area removed;
   - weight per block; coverage per block;
   - keep only the eight output columns (no intersection geometries).
6. **Grid reuse across years** — the fishnet and crosswalk are built once, from the first configured year's validated reference grid. For each other configured year, compare its reference raster with the first year's using `validate_same_grid` (Feature 3's import). Record the result in the QC JSON. The outputs are reused for a year only if its grid is identical; otherwise the run stops with an error for that year.
7. **QC** — `src/qc.py` Feature 4 section:
   - essential: unique `cell_id`; unique (`block_geoid`, `cell_id`); weights sum to 1 within `weight_tol` per block; population of the unique blocks equals the Census total; no populated block missing from the crosswalk.
   - warning: blocks below `low_coverage_threshold` (count and list).
   - informational: the number of generated fishnet cells, reported without comparison to any predefined count.
8. **Publish** — write to `.tmp`, then rename. A failed essential check writes no outputs and exits non-zero. The QC JSON records the failure.
9. **Workflow** — `Snakefile`: rule `build_crosswalk` (wildcards `vintage`, `state_fips` from the Census targets). Inputs: Feature 2 `blocks.parquet`; Feature 3 `raster_validation.csv` for the reference year; `conf/crosswalk.yaml`, `conf/census.yaml`, `conf/prism_ppt.yaml`, `src/crosswalk.py`, `src/qc.py`. Outputs: fishnet, crosswalk, QC JSON. Any change to those inputs rebuilds Feature 4 only. Features 1–3 rules keep their inputs unchanged, so they do not rerun.
10. **Tests** — `tests/test_crosswalk.py`, three synthetic tests on a 4 × 4 grid and small blocks:
    - a block split across cells: IDs unique, weights sum to 1, coverage 1, pairs unique, population kept;
    - a sliver below 10 m² removed and a block below 0.99 coverage reported as a warning;
    - a populated block with no retained overlap: run fails and nothing is published.

## Skills applied

- **raster-processing:** `inspect_raster` (imported by path); `cell_polygon` and the ID formula (local copy, decision Q3).
- **areal-overlay:** densification, equal-area measurement, sliver removal, weight and coverage definitions, validation list. Guidance only.
- **python-pipeline-style:** Hydra entry point, `pathlib`, logging, QC in `qc.py`, pytest.
- **snakemake-workflow:** wildcard rule, declared outputs, incremental reruns.

## Configuration

| Parameter | Value | File | Decision |
|-----------|-------|------|----------|
| Fishnet margin | 2 cells | `crosswalk.yaml` | D2 |
| Densify | 0.0001° | `crosswalk.yaml` | D4 |
| Area CRS | EPSG:5070 | `crosswalk.yaml` | D4 |
| Minimum overlap | 10 m² | `crosswalk.yaml` | D5 |
| Weight tolerance | 1.0e-9 | `crosswalk.yaml` | D6 |
| Low-coverage threshold | 0.99 | `crosswalk.yaml` | D7 |
| Vintage, state | 2020, `"53"` | `census.yaml` | D11 |
| Output roots | `intermediate_root`, `metadata_root` | `datapaths.yaml` | D11 |

## Data manifest

| Dataset | Version | Location | Transformations | Stage |
|---------|---------|----------|-----------------|-------|
| Census blocks (Feature 2) | 2020, WA | `data/intermediate/census/2020/53/blocks.parquet` | Read only | crosswalk |
| PRISM reference grid (Feature 3) | 2024-01-01 | `data/raw/prism/ppt/2024/…zip` | Read only | crosswalk |
| Fishnet | window of reference grid | `data/intermediate/crosswalk/2020/53/fishnet.parquet` | Densified and projected for intersection only | crosswalk |
| Block–cell crosswalk | per run | `data/intermediate/crosswalk/2020/53/block_cell_crosswalk.parquet` | Weights and coverage added | crosswalk |
| QC report | per run | `data/metadata/crosswalk/2020/53/qc_report.json` | None | QC |

## Traceability

| Spec item | Element | Task |
|-----------|---------|------|
| D1 | `reference_grid`; cross-year `validate_same_grid` | T02, T06 |
| D2 | `window` | T03 |
| D3 | `cell_polygon`, `build_fishnet` | T03 |
| D4 | densify and projection in `build_crosswalk` | T04 |
| D5 | sliver removal and count | T04 |
| D6 | weights | T04 |
| D7 | coverage | T04 |
| D8 | output columns | T04 |
| D9 | essential checks in `qc.py` | T05 |
| D10 | low-coverage warning in `qc.py` | T05 |
| D11 | publish step | T05 |
| D12 | `Snakefile` rule | T07 |
| D13 | Hydra config | T01 |
| AC1–AC3 | fishnet and crosswalk checks | T06 |
| AC4 | population check | T06, T08 |
| AC5 | missing populated block test | T06 |
| AC6 | low-coverage warning test and real run | T06, T08 |
| AC7 | fishnet cell count reported (no benchmark comparison) | T08 |
| AC8 | unchanged inputs | T08 |
| AC9 | `snakemake -n` | T08 |
| AC10 | config audit | T08 |

## Validation

- **Tests:** `pytest` in `prism-spaceagg`, including the 11 existing tests.
- **Real run:** Washington 2020. Report the population, the weight check, the fishnet cell count, and the number of blocks below 99% coverage. No count is assumed in advance.
- **Originals:** SHA-256 and mtime of the ZIPs, blocks, and manifests before and after.
- **Incremental:** `snakemake -n` plans nothing after the run.

## Risks

| Risk | Mitigation |
|------|------------|
| Densifying cells adds many vertices | Only window cells are densified; monitor memory and time on the real run. |
| Intersection of about 158k blocks is slow | Bounding-box sjoin first; a single run for Washington. |
| Excluding slivers drops a block completely | The populated-block check fails the run and publishes nothing. |
| Local `cell_polygon` copy drifts from the Skill | The copy is four lines; its cell order and ID formula are checked against the Skill in the code review. No extra test. |

## Alternatives considered

- Import `cell_polygon` from the Skill script: rejected; it imports Fiona (decision Q3).
- Allocate population in the crosswalk: rejected; allocation is Feature 5 (decision D8).
- Full-raster fishnet: rejected; window only.
