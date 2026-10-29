"""Yearly county precipitation totals and means from the Feature 5 county-day series, with a county map."""

import json
import logging
from pathlib import Path

import geopandas as gpd
import hydra
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, PowerNorm  # noqa: E402
from omegaconf import DictConfig  # noqa: E402

from census_blocks import state_key  # noqa: E402
from county_precip import DAY_DEFINITION, UNITS  # noqa: E402
from download_prism import expected_dates  # noqa: E402
from qc import check_yearly, write_json_atomic  # noqa: E402

logger = logging.getLogger(__name__)

SURFACE = "#ffffff"
DISPLAY_CRS = "EPSG:4269"  # original Census CRS, shown without reprojection (north-up)


def yearly_values(daily: pd.DataFrame, year: int, days: list) -> pd.DataFrame:
    """Sum the daily county means and divide by the expected days; keep counts for the completeness check."""
    grouped = daily.groupby("county_geoid")
    total = grouped["precip_mm"].sum()
    return pd.DataFrame({
        "county_geoid": total.index.to_numpy(),
        "year": year,
        "population": grouped["population_total"].first().to_numpy(),
        "days_observed": grouped["precip_mm"].count().to_numpy(),
        "days_expected": len(days),
        "precip_total_mm": total.to_numpy(),
        "precip_mean_mm": (total / len(days)).to_numpy(),
    })


def county_outlines(blocks: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Dissolve Feature 2 blocks by county GEOID to get one outline per county."""
    return blocks[["county_geoid", "geometry"]].dissolve(by="county_geoid").reset_index()


def land_outlines(raw_zip: Path) -> gpd.GeoDataFrame:
    """Display outlines from the original block geometries: dissolve land blocks only, so water-only blocks
    leave the coastline, Puget Sound, and lake gaps. Not simplified; used only for the map."""
    blocks = gpd.read_file(f"zip://{raw_zip}", columns=["STATEFP20", "COUNTYFP20", "ALAND20", "geometry"])
    if blocks.crs != DISPLAY_CRS:
        raise ValueError(f"Census blocks are {blocks.crs}; expected {DISPLAY_CRS} for the map")
    land = blocks[blocks["ALAND20"] > 0].assign(county_geoid=lambda frame: frame["STATEFP20"] + frame["COUNTYFP20"])
    return land[["county_geoid", "geometry"]].dissolve(by="county_geoid").reset_index()


def draw_map(outlines: gpd.GeoDataFrame, yearly: pd.DataFrame, path: Path, state_name: str, year: int) -> None:
    """Write a county choropleth of mean daily precipitation in EPSG:4269 with a vertical colorbar in mm/day."""
    merged = outlines.merge(yearly[["county_geoid", "precip_mean_mm"]], on="county_geoid", how="left")
    cmap = LinearSegmentedColormap.from_list("blues_light", plt.cm.Blues(np.linspace(0.2, 1, 256)))
    norm = PowerNorm(gamma=0.5, vmin=0, vmax=yearly["precip_mean_mm"].max())
    # Degrees of longitude shrink with latitude; scale the y-axis so the state keeps its true proportions.
    mid_latitude = np.deg2rad(merged.total_bounds[[1, 3]].mean())
    fig, ax = plt.subplots(figsize=(7, 4.6), facecolor=SURFACE, layout="constrained")
    ax.set_facecolor(SURFACE)
    merged.plot(column="precip_mean_mm", ax=ax, cmap=cmap, norm=norm, edgecolor="#555555", linewidth=0.5,
                legend=True, legend_kwds={"label": "mm/day", "orientation": "vertical",
                                          "shrink": 0.8, "pad": 0.02})
    ax.set_aspect(1 / np.cos(mid_latitude))
    ax.set_axis_off()
    ax.set_title("Mean Daily Population-Weighted Precipitation (mm/day)\n"
                 f"{state_name} State | {year}", fontsize=14, linespacing=1.4, pad=4)
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor=SURFACE)
    plt.close(fig)


def run_year(cfg: DictConfig, year: int) -> None:
    """Build the yearly table, check it, and publish the Parquet, QC JSON, and map after QC passes."""
    paths, prism, census = cfg.paths, cfg.prism, cfg.census
    vintage = int(census.vintage)
    state = state_key(census.state_fips)
    days = expected_dates(year, prism.start_date, prism.end_date)

    daily_dir = Path(paths.output_root) / "prism_county_daily" / str(vintage) / state
    daily_qc = json.loads((Path(paths.metadata_root) / "prism_county_daily" / str(vintage) / state
                           / f"county_daily_{year}_qc.json").read_text())
    if daily_qc["status"] != "pass":
        raise ValueError(f"Feature 5 QC for {year} did not pass; yearly results are not built")
    daily = pd.read_parquet(daily_dir / f"county_daily_{year}.parquet")

    blocks = gpd.read_parquet(Path(paths.intermediate_root) / "census" / str(vintage) / state / "blocks.parquet",
                              columns=["county_geoid", "geometry"])
    outlines = county_outlines(blocks)
    yearly = yearly_values(daily, year, days)

    qc_path = Path(paths.metadata_root) / "prism_county_yearly" / str(vintage) / state / f"county_yearly_{year}_qc.json"
    try:
        summary = check_yearly(yearly, daily, sorted(blocks["county_geoid"].unique()), outlines, len(days))
    except ValueError as error:
        write_json_atomic({"year": year, "status": "fail", "error": str(error)}, qc_path)
        raise

    metadata = {"units": f"precip_total_mm: mm; precip_mean_mm: {UNITS}/day",
                "population_year": str(vintage), "day_definition": DAY_DEFINITION,
                "dataset": "PRISM daily ppt, 800 m, yearly from Feature 5 county series"}
    out_dir = Path(paths.output_root) / "prism_county_yearly" / str(vintage) / state
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"county_yearly_{year}.parquet"
    tmp = final.with_name(final.name + ".tmp")
    table = pa.Table.from_pandas(yearly, preserve_index=False).replace_schema_metadata(
        {key: value.encode() for key, value in metadata.items()})
    pq.write_table(table, tmp)

    figure_dir = Path(paths.output_root) / "figures" / str(vintage) / state
    figure_dir.mkdir(parents=True, exist_ok=True)
    figure_tmp = figure_dir / f"county_mean_daily_precip_{year}.tmp.png"
    raw_zip = Path(paths.raw_root) / "census" / str(vintage) / state / census.filename.format(
        vintage=vintage, state_fips=state)
    draw_map(land_outlines(raw_zip), yearly, figure_tmp, census.state_name, year)

    tmp.replace(final)
    figure_tmp.replace(figure_dir / f"county_mean_daily_precip_{year}.png")
    write_json_atomic({"year": year, "status": "pass", **metadata, **summary}, qc_path)
    logger.info("Year %d: published %d county rows to %s", year, len(yearly), final)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    run_year(cfg, int(cfg.year))


if __name__ == "__main__":
    main()
