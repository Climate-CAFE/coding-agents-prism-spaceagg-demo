"""Population-weighted daily county precipitation from PRISM rasters and the block–cell crosswalk."""

import logging
import zipfile
from pathlib import Path

import hydra
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from omegaconf import DictConfig
from rasterio.windows import Window

from census_blocks import state_key
from crosswalk import reference_grids, require_validated_year
from download_prism import expected_dates
from qc import check_county_daily, write_json_atomic

logger = logging.getLogger(__name__)

# Fixed dataset conventions, recorded in the output metadata rather than in configuration.
UNITS = "mm"
DAY_DEFINITION = "PRISM daily total for the 24 hours ending 12:00 UTC; date is the PRISM file date"


def cell_window(cell_ids: np.ndarray, width: int) -> Window:
    """Return the raster window covering the cells, using row = (cell_id - 1) // width and col = (cell_id - 1) % width."""
    rows = (cell_ids - 1) // width
    cols = (cell_ids - 1) % width
    return Window.from_slices((int(rows.min()), int(rows.max()) + 1), (int(cols.min()), int(cols.max()) + 1))


def read_window(zip_path: Path, window: Window) -> tuple[np.ndarray, float]:
    """Read the window of the single GeoTIFF inside a ZIP, in place. Raise if the file is missing or unreadable."""
    if not zip_path.exists():
        raise FileNotFoundError(f"Missing PRISM raster: {zip_path}")
    with zipfile.ZipFile(zip_path) as archive:
        members = [name for name in archive.namelist() if name.endswith(".tif")]
    if len(members) != 1:
        raise ValueError(f"Expected one GeoTIFF in {zip_path.name}, found {len(members)}")
    with rasterio.open(f"/vsizip/{zip_path}/{members[0]}") as ds:
        return ds.read(1, window=window), ds.nodata


def block_means(table: pd.DataFrame, values: np.ndarray, row0: int, col0: int, nodata: float, n_blocks: int):
    """Return each block's area-weighted precipitation over valid cells, and its valid weight (coverage)."""
    x = values[table["row"].to_numpy() - row0, table["col"].to_numpy() - col0].astype("float64")
    valid = np.isfinite(x) & (x != nodata)
    weight = np.where(valid, table["area_weight"].to_numpy(), 0.0)
    weighted = weight * np.where(valid, x, 0.0)
    codes = table["block_index"].to_numpy()
    coverage = np.bincount(codes, weights=weight, minlength=n_blocks)
    total = np.bincount(codes, weights=weighted, minlength=n_blocks)
    precip = np.divide(total, coverage, out=np.full(n_blocks, np.nan), where=coverage > 0)
    return precip, coverage


def county_means(blocks: pd.DataFrame, precip: np.ndarray) -> pd.DataFrame:
    """Return population-weighted precipitation per county over blocks with valid values, and population coverage."""
    valid = ~np.isnan(precip)
    population = blocks["population"].to_numpy()
    frame = pd.DataFrame({
        "county_geoid": blocks["county_geoid"].to_numpy(),
        "population_total": population,
        "population_valid": np.where(valid, population, 0),
        "weighted_sum": np.where(valid, population * np.nan_to_num(precip), 0.0),
    })
    sums = frame.groupby("county_geoid").sum()
    valid_pop = sums["population_valid"].to_numpy()
    total_pop = sums["population_total"].to_numpy()
    precip_mm = np.divide(sums["weighted_sum"].to_numpy(), valid_pop,
                          out=np.full(len(sums), np.nan), where=valid_pop > 0)
    coverage = np.divide(valid_pop, total_pop, out=np.zeros(len(sums)), where=total_pop > 0)
    return pd.DataFrame({
        "county_geoid": sums.index.to_numpy(),
        "precip_mm": precip_mm,
        "population_total": total_pop.astype("int64"),
        "population_valid": valid_pop.astype("int64"),
        "population_coverage": coverage,
    })


def prepare_crosswalk(crosswalk: pd.DataFrame, width: int) -> tuple[pd.DataFrame, Window, pd.DataFrame, int]:
    """Add raster row, column, and block index to the crosswalk; return it with its window and block table."""
    table = crosswalk.copy()
    table["row"] = (table["cell_id"] - 1) // width
    table["col"] = (table["cell_id"] - 1) % width
    table["block_index"] = pd.factorize(table["block_geoid"])[0]
    window = cell_window(table["cell_id"].to_numpy(), width)
    blocks = table.drop_duplicates("block_index").sort_values("block_index")[["county_geoid", "population"]]
    return table, window, blocks.reset_index(drop=True), len(blocks)


def run_year(cfg: DictConfig, year: int, reference: dict) -> None:
    """Aggregate one year, check it, and publish the county-day Parquet and QC JSON atomically."""
    paths, prism = cfg.paths, cfg.prism
    census = cfg.census
    vintage = int(census.vintage)
    state = state_key(census.state_fips)
    require_validated_year(paths, prism, year)

    crosswalk = pd.read_parquet(Path(paths.intermediate_root) / "crosswalk" / str(vintage) / state / "block_cell_crosswalk.parquet")
    table, window, blocks, n_blocks = prepare_crosswalk(crosswalk, reference["width"])
    days = expected_dates(year, prism.start_date, prism.end_date)
    raw_dir = Path(paths.raw_root) / "prism" / prism.variable / str(year)

    frames = []
    for day in days:
        values, nodata = read_window(raw_dir / f"{prism.file_prefix}{day:%Y%m%d}.zip", window)
        precip, _ = block_means(table, values, window.row_off, window.col_off, nodata, n_blocks)
        county = county_means(blocks, precip)
        county.insert(1, "date", day)
        frames.append(county)
    result = pd.concat(frames, ignore_index=True)

    counties = sorted(blocks["county_geoid"].unique())
    qc_path = Path(paths.metadata_root) / "prism_county_daily" / str(vintage) / state / f"county_daily_{year}_qc.json"
    try:
        summary = check_county_daily(result, days, counties)
    except ValueError as error:
        write_json_atomic({"year": year, "status": "fail", "error": str(error)}, qc_path)
        raise

    out_dir = Path(paths.output_root) / "prism_county_daily" / str(vintage) / state
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"county_daily_{year}.parquet"
    tmp = final.with_name(final.name + ".tmp")
    metadata = {"units": UNITS, "day_definition": DAY_DEFINITION, "dataset": "PRISM daily ppt, 800 m",
                "weighting": "block: crosswalk area_weight over valid cells; county: block population over valid blocks"}
    table_out = pa.Table.from_pandas(result, preserve_index=False).replace_schema_metadata(
        {key: value.encode() for key, value in metadata.items()})
    pq.write_table(table_out, tmp)
    tmp.replace(final)

    write_json_atomic({"year": year, "status": "pass", **metadata, **summary}, qc_path)
    logger.info("Year %d: published %d county-day rows to %s", year, len(result), final)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    reference, _ = reference_grids(cfg.paths, cfg.prism, cfg.crosswalk.weight_tol)
    run_year(cfg, int(cfg.year), reference)


if __name__ == "__main__":
    main()
