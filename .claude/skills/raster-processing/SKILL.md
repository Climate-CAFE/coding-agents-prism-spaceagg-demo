---
name: raster-processing
description: Use when discovering or inspecting raster time series, validating grid alignment, generating raster-cell fishnets, or preparing raster grids for spatial aggregation.
---

# Raster Processing

Inspect and prepare gridded environmental data for spatial analysis. Follow `AGENTS.md` and the approved feature specification for scientific decisions.

## Workflow

1. **Discover.** Identify raster files for the approved variable and period. Use configured paths, naming conventions, and expected dates.

2. **Inspect.** Record each raster's driver, dimensions, CRS, affine transform, resolution, bounds, data type, and NoData value.

   ```bash
   python .claude/skills/raster-processing/scripts/inspect_raster.py <rasters...> --tol 1e-9
   ```

   The script returns JSON, comparing subsequent rasters against the first raster.

3. **Validate grid alignment.**
   - Compare CRS, dimensions, and the full affine transform.
   - Report NoData differences separately from grid mismatches.
   - Do not silently reproject or resample mismatched rasters.
   - Verify alignment before reusing cell geometry or spatial mappings across dates.

4. **Generate a fishnet when required.** Create raster-cell polygons using the full affine transform.

   ```bash
   python .claude/skills/raster-processing/scripts/create_fishnet.py <raster.tif> <fishnet.gpkg> --chunk-rows 50
   ```

   - Assign stable IDs using `cell_id = row * width + col + 1`.
   - Preserve the raster's CRS.
   - Avoid generating an unnecessary full-raster fishnet for large datasets.
   - Reuse the fishnet across dates when grids match.

5. **Verify.**
   - Check unique cell IDs and valid polygon geometries.
   - Spot-check cell locations against Rasterio row/column indexing.
   - Record grid differences and unresolved issues.

## Guardrails

- Preserve native raster values; treat NoData as missing, not zero.
- Use the full affine transform; do not assume cells are square or axis-aligned.
- Use stable cell IDs for mapping:

  `row = (cell_id - 1) // width`

  `col = (cell_id - 1) % width`

- Read large rasters in windows or chunks when practical.
- Keep grid-alignment checks separate from NoData and scientific-value validation.
- Do not change CRS, resolution, or grid geometry without approval.
- Treat reference scripts' function signatures and output formats as stable when reused by pipeline code.

## Reference Scripts

- `scripts/inspect_raster.py` — inspect raster metadata and compare grid alignment.
- `scripts/create_fishnet.py` — generate cell-aligned polygons in a GeoPackage.

Reuse these utilities when implementing pipeline stages in `src/`. Keep dataset-specific processing, orchestration, and QC in the production pipeline.