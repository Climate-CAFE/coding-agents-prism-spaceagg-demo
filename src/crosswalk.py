"""Build the PRISM fishnet window and the Census block–cell crosswalk with area weights."""

import csv
import logging
import math
from pathlib import Path

import geopandas as gpd
import hydra
import pandas as pd
import shapely
from omegaconf import DictConfig
from rasterio.transform import Affine

import validate_rasters  # noqa: F401 (puts the raster-processing Skill scripts on sys.path)
from census_blocks import state_key
from download_prism import expected_dates
from inspect_raster import validate_same_grid
from qc import check_crosswalk, check_reference_metadata, write_json_atomic
from validate_rasters import read_record

logger = logging.getLogger(__name__)


def cell_polygon(transform: Affine, row: int, col: int) -> shapely.Polygon:
    """Return the cell polygon from the affine transform. Local copy of the raster-processing Skill's cell_polygon()."""
    corners = [transform @ (col, row), transform @ (col + 1, row), transform @ (col + 1, row + 1), transform @ (col, row + 1)]
    return shapely.Polygon(corners)


def window_cells(bounds: tuple, transform: Affine, width: int, height: int, margin: int) -> tuple[int, int, int, int]:
    """Return (row_start, row_end, col_start, col_end) covering the bounds plus margin, clipped to the raster."""
    minx, miny, maxx, maxy = bounds
    inverse = ~transform
    corners = [inverse @ (x, y) for x in (minx, maxx) for y in (miny, maxy)]
    rows = [row for _, row in corners]
    cols = [col for col, _ in corners]
    row_start = max(math.floor(min(rows)) - margin, 0)
    row_end = min(math.ceil(max(rows)) + margin, height)
    col_start = max(math.floor(min(cols)) - margin, 0)
    col_end = min(math.ceil(max(cols)) + margin, width)
    return row_start, row_end, col_start, col_end


def build_fishnet(transform: Affine, width: int, window: tuple, crs: str) -> gpd.GeoDataFrame:
    """Return one polygon per window cell, with cell_id on the full raster grid."""
    row_start, row_end, col_start, col_end = window
    cells = [(row, col) for row in range(row_start, row_end) for col in range(col_start, col_end)]
    return gpd.GeoDataFrame(
        {"cell_id": [row * width + col + 1 for row, col in cells]},
        geometry=[cell_polygon(transform, row, col) for row, col in cells],
        crs=crs,
    )


def densify_and_project(frame: gpd.GeoDataFrame, crw: DictConfig) -> gpd.GeoDataFrame:
    """Densify edges in the source CRS, then project to the equal-area CRS."""
    frame = frame.copy()
    frame["geometry"] = shapely.segmentize(frame.geometry.values, crw.densify_deg)
    return frame.to_crs(crw.area_crs)


def build_crosswalk(blocks: gpd.GeoDataFrame, fishnet: gpd.GeoDataFrame, crw: DictConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Intersect blocks with cells, drop slivers, and return the crosswalk, per-block coverage, and sliver totals."""
    blocks = blocks[["block_geoid", "county_geoid", "population", "geometry"]].reset_index(drop=True)
    left = densify_and_project(blocks, crw)
    right = densify_and_project(fishnet.reset_index(drop=True), crw)

    pairs = gpd.sjoin(left, right[["cell_id", "geometry"]], how="inner", predicate="intersects")
    overlap = shapely.intersection(left.geometry.loc[pairs.index].values, right.geometry.loc[pairs["index_right"]].values)
    area = shapely.area(overlap)
    keep = area > crw.min_overlap_m2
    slivers = {"slivers_removed": int((~keep).sum()), "sliver_area_m2": float(area[~keep].sum())}

    table = pd.DataFrame({
        "block_geoid": left["block_geoid"].loc[pairs.index].values[keep],
        "county_geoid": left["county_geoid"].loc[pairs.index].values[keep],
        "cell_id": right["cell_id"].loc[pairs["index_right"]].values[keep],
        "population": left["population"].loc[pairs.index].values[keep],
        "overlap_area_m2": area[keep],
    })
    table["area_weight"] = table["overlap_area_m2"] / table.groupby("block_geoid")["overlap_area_m2"].transform("sum")

    retained = table.groupby("block_geoid")["overlap_area_m2"].sum()
    block_area = left.set_index("block_geoid").geometry.area
    coverage = (retained.reindex(block_area.index).fillna(0.0) / block_area).rename("coverage")
    table["block_coverage"] = table["block_geoid"].map(coverage)

    block_qc = left[["block_geoid", "population"]].assign(coverage=coverage.values)
    columns = ["block_geoid", "county_geoid", "cell_id", "population", "overlap_area_m2", "area_weight", "block_coverage"]
    return table[columns], block_qc, slivers


def reference_record(paths: DictConfig, prism: DictConfig, year: int) -> dict | None:
    """Inspect the first expected raster of a year. Return the record, or None if it cannot be read."""
    raw_dir = Path(paths.raw_root) / "prism" / prism.variable / str(year)
    day = expected_dates(year, prism.start_date, prism.end_date)[0]
    record, _ = read_record(raw_dir / f"{prism.file_prefix}{day:%Y%m%d}.zip")
    return record


def require_validated_year(paths: DictConfig, prism: DictConfig, year: int) -> None:
    """Raise if the year's Feature 3 validation report is missing or lists any issue."""
    report = Path(paths.metadata_root) / "prism" / prism.variable / str(year) / "raster_validation.csv"
    with report.open(newline="") as handle:
        issues = [row["issues"] for row in csv.DictReader(handle) if row["issues"]]
    if issues:
        raise ValueError(f"Raster validation for {year} lists {len(issues)} issues; run stops")


def reference_grids(paths: DictConfig, prism: DictConfig, tol: float) -> tuple[dict, dict]:
    """Return the first year's reference grid and a record of which other years share it."""
    years = [int(year) for year in prism.years]
    require_validated_year(paths, prism, years[0])
    reference = reference_record(paths, prism, years[0])
    if not check_reference_metadata(reference, tol):
        raise ValueError(f"Reference raster for {years[0]} is unreadable, rotated, or has no NoData")

    grid_checks = {}
    for year in years[1:]:
        record = reference_record(paths, prism, year)
        issues = [] if record is None else validate_same_grid(reference, record, tol)
        if issues:
            raise ValueError(f"Grid for {year} is not identical to {years[0]}: {issues}")
        grid_checks[str(year)] = "identical"
    return reference, grid_checks


def run(cfg: DictConfig) -> None:
    """Build the fishnet and crosswalk for the configured state, run QC, and publish if essential checks pass."""
    census, crw = cfg.census, cfg.crosswalk
    vintage = int(census.vintage)
    state = state_key(census.state_fips)
    blocks_path = Path(cfg.paths.intermediate_root) / "census" / str(vintage) / state / "blocks.parquet"
    out_dir = Path(cfg.paths.intermediate_root) / "crosswalk" / str(vintage) / state
    qc_path = Path(cfg.paths.metadata_root) / "crosswalk" / str(vintage) / state / "qc_report.json"

    blocks = gpd.read_parquet(blocks_path)
    reference, grid_checks = reference_grids(cfg.paths, cfg.prism, crw.weight_tol)
    if not blocks.crs.equals(reference["crs"]):
        raise ValueError(f"Block CRS {blocks.crs} does not match raster CRS {reference['crs']}")

    transform = Affine(*reference["transform"])
    window = window_cells(blocks.total_bounds, transform, reference["width"], reference["height"], crw.fishnet_margin_cells)
    fishnet = build_fishnet(transform, reference["width"], window, reference["crs"])
    table, block_qc, slivers = build_crosswalk(blocks, fishnet, crw)
    report = {"vintage": vintage, "state_fips": state, "reference_grid_checks": grid_checks,
              "fishnet_window": list(window), **slivers}
    try:
        summary = check_crosswalk(fishnet, table, block_qc, crw.weight_tol, crw.low_coverage_threshold)
    except ValueError as error:
        write_json_atomic({**report, "status": "fail", "error": str(error)}, qc_path)
        raise

    out_dir.mkdir(parents=True, exist_ok=True)
    fishnet_tmp, crosswalk_tmp = out_dir / "fishnet.parquet.tmp", out_dir / "block_cell_crosswalk.parquet.tmp"
    fishnet.to_parquet(fishnet_tmp)
    table.to_parquet(crosswalk_tmp, index=False)
    fishnet_tmp.replace(out_dir / "fishnet.parquet")
    crosswalk_tmp.replace(out_dir / "block_cell_crosswalk.parquet")
    write_json_atomic({**report, "status": "pass", **summary}, qc_path)
    logger.info("Published %d fishnet cells and %d crosswalk rows", len(fishnet), len(table))


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    run(cfg)


if __name__ == "__main__":
    main()
