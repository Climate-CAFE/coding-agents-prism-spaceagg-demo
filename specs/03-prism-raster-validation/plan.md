# Plan: PRISM raster inspection and validation

- **Spec:** `specs/03-prism-raster-validation/spec.md` (draft 1, approved 2026-10-28)
- **Status:** awaiting approval (gate 2)

## Approach

One script reads each configured date's GeoTIFF from its Feature 1 ZIP through `/vsizip/`, compares it with the reference (first expected date) using the Skill's `inspect_raster` and `validate_same_grid`, adds NoData and rotation checks, and writes `raster_validation.csv`. Nothing is extracted or modified. A Snakemake rule per year depends on Feature 1's manifest.

## Layout

```
src/validate_rasters.py        # NEW: read, compare, write CSV (Hydra entry point)
src/qc.py                      # ADD "Feature 3: PRISM rasters" section (issue codes, rotation, NoData)
conf/prism_ppt.yaml            # ADD transform_tol: 1.0e-9
environment.yaml               # ADD rasterio (conda-forge)
Snakefile                      # ADD validate_prism_rasters rule (Feature 1 rules unchanged)
tests/test_validate_rasters.py # NEW: 3 offline tests
```

## Modules

1. **Config** — `prism.transform_tol: 1.0e-9` in `conf/prism_ppt.yaml`. Paths come from `datapaths.yaml` and `prism.*` as in Feature 1.
2. **Read** — `validate_rasters.main(cfg)` per year. For each expected date from `download_prism.expected_dates`, the member is the single `.tif` in the ZIP at `raw_root/prism/ppt/<year>/prism_ppt_us_30s_<date>.zip`. Open as `/vsizip/<zip>/<member>`. Call `inspect_raster` (Skill) to get driver, CRS, size, transform, and NoData. A missing ZIP or an open failure is recorded as `missing_file` or `unreadable`.
3. **Compare** — first expected date is the reference (D2). Call `validate_same_grid(reference, record, tol)` (Skill, D4, exact CRS and size). Add checks in `qc.py`: rotated transform (b or d beyond tol), NoData missing or mismatch against the reference NoData (D6), and an invalid reference (unreadable, rotated, or NoData missing).
4. **Output** — one row per expected date: `date`, `file`, `issues` (`;`-joined codes), `matches_reference` (TRUE, FALSE, or blank, per D8), and key metadata (CRS, width, height, resolution, NoData). Written atomically to `data/metadata/prism/ppt/<year>/raster_validation.csv`. Report-only: exit 0 (D13).
5. **Workflow** — rule `validate_prism_rasters` (wildcard `year`). Input: Feature 1 `manifest.csv`. Output: `raster_validation.csv`. Log to `logs/`.
6. **Tests** — `tests/test_validate_rasters.py`, three offline tests on synthetic GeoTIFFs in ZIPs:
   - all dates match: TRUE for all rows.
   - one missing ZIP, one unreadable file, one shape mismatch, one NoData mismatch: correct codes and FALSE or blank values; run still exits 0.
   - invalid reference (rotated transform): all rows blank, `invalid_reference_metadata`.

## Skills applied

- **raster-processing:** `inspect_raster`, `validate_same_grid` (imported by path, D11). No fishnet or resampling needed.
- **python-pipeline-style:** Hydra entry point, `pathlib`, logging, tests.
- **snakemake-workflow:** per-year rule, declared outputs, incremental on the manifest.

## Configuration

| Parameter | Value | File | Decision |
|-----------|-------|------|----------|
| Transform tolerance | 1.0e-9 | `prism_ppt.yaml` | D4 |
| Reference date | first expected date | derived (`prism.start_date` or Jan 1) | D2 |
| Metadata and raw roots | from `datapaths.yaml` | `datapaths.yaml` | D10 |

## Data manifest

| Dataset | Version | Location | Transformations | Stage |
|---------|---------|----------|-----------------|-------|
| PRISM daily ppt GeoTIFF | Feature 1 download | inside `data/raw/prism/ppt/<year>/*.zip` | None (read only) | validation |
| Raster validation report | per run | `data/metadata/prism/ppt/<year>/raster_validation.csv` | None | validation |

## Traceability

| Spec item | Element | Task |
|-----------|---------|------|
| D1 | read via `/vsizip/` in `validate_rasters` | T02 |
| D2 | reference = first expected date | T02, T03 |
| D3, D4 | `validate_same_grid` (Skill) | T03 |
| D5 | `qc.check_rotation` | T04 |
| D6 | `qc.check_nodata` | T04 |
| D7 | issue codes in `qc.py` | T04 |
| D8 | `matches_reference` logic | T05 |
| D9 | `qc.check_reference` (invalid reference) | T04 |
| D10 | CSV write in `validate_rasters` | T05 |
| D11 | import from skill path | T02 |
| D12 | `Snakefile` rule | T06 |
| D13 | exit 0 on data issues | T05, T07 |
| AC1 | one row per date | T07 |
| AC2 | reference is first configured date | T07 |
| AC3 | issue codes per problem | T07 |
| AC4 | blank `matches_reference` | T07 |
| AC5 | real 2024 run | T08 |
| AC6 | ZIPs unchanged (SHA-256, mtime) | T08 |
| AC7 | incremental rerun plans nothing | T08 |
| AC8 | config only | T08 |

## Validation

- **Tests:** `pytest` in `prism-spaceagg`, including the eight existing tests.
- **Real run:** 2024. Expect 366 rows, all readable, all TRUE, and a single NoData value across dates. Record the NoData value in status.
- **Originals:** SHA-256 and mtime of the 2024 ZIPs before and after.
- **Incremental:** `snakemake -n` plans nothing after the run.

## Risks

| Risk | Mitigation |
|------|------------|
| Reading 366 GeoTIFFs through `/vsizip/` is slow | Read metadata only (no pixel reads); time the run. |
| `rasterio` install conflicts with geopandas or pyogrio | Install from conda-forge and rerun the eight tests. |
| Reference NoData is missing | Reported as `invalid_reference_metadata`; the CSV still records every date. |

## Alternatives considered

- Copy the Skill's functions into `src/`: rejected by your decision (D11).
- Fail the run on any mismatch: rejected by your decision (D13).
