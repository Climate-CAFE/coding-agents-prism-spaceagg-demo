# Tasks: PRISM raster inspection and validation

Check a box only after its definition of done runs.

- [x] **T01 — Config and package.** Serves: D4, AC8. Files: `environment.yaml`, `conf/prism_ppt.yaml`. DoD: `rasterio` installed in `prism-spaceagg`; `prism.transform_tol` composes in Hydra. DoD met: rasterio 1.5.2 (GDAL 3.13.3) installed; `transform_tol` in config.
- [x] **T02 — Read and reference.** Serves: D1, D2, D11. File: `src/validate_rasters.py`. DoD: `/vsizip/` read of one date via imported `inspect_raster`; reference is the first expected date. DoD met: `/vsizip/` read via imported `inspect_raster`; reference is first expected date.
- [x] **T03 — Grid comparison.** Serves: D3, D4. File: `src/validate_rasters.py`. DoD: imported `validate_same_grid` gives crs, shape, transform codes. DoD met: imported `validate_same_grid` returns crs, shape, and transform codes.
- [x] **T04 — QC section.** Serves: D5, D6, D7, D9. File: `src/qc.py` (Feature 3 section). DoD: rotation, NoData, and invalid-reference checks return the issue codes. DoD met: rotation, NoData, and invalid-reference checks in `qc.py`.
- [x] **T05 — Output and exit.** Serves: D8, D10, D13. File: `src/validate_rasters.py`. DoD: `raster_validation.csv` written atomically; data issues exit 0. DoD met: CSV written atomically; data issues exit 0.
- [x] **T06 — Snakefile.** Serves: D12. File: `Snakefile`. DoD: rule `validate_prism_rasters` depends on the Feature 1 manifest; `snakemake -n` plans only it when its output is missing. DoD met: `validate_prism_rasters` depends on the Feature 1 manifest; dry run plans only it when its output is missing.
- [x] **T07 — Tests.** Serves: AC1–AC4. File: `tests/test_validate_rasters.py` (3 tests). DoD: `pytest` passes, including the eight existing tests. DoD met: `pytest` 11 passed (8 existing + 3 new).
- [x] **T08 — Real run.** Serves: AC5–AC7. DoD: 366 rows, all readable, `matches_reference` TRUE; ZIP SHA-256 and mtime unchanged; rerun plans nothing. DoD met: 366 rows, all TRUE, no issues; ZIP SHA-256 matches Feature 1 manifest for all 366; mtime/size/inode unchanged; rerun plans nothing.
