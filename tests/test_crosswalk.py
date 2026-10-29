import geopandas as gpd
import pytest
from omegaconf import OmegaConf
from rasterio.transform import Affine
from shapely.geometry import box

from crosswalk import build_crosswalk, build_fishnet, window_cells
from qc import check_crosswalk

TRANSFORM = Affine(0.01, 0, -120.0, 0, -0.01, 47.04)  # 4 x 4 grid of 0.01° cells
CRW = OmegaConf.create({"densify_deg": 0.0001, "area_crs": "EPSG:5070", "min_overlap_m2": 10,
                        "weight_tol": 1.0e-9, "low_coverage_threshold": 0.99, "fishnet_margin_cells": 0})


def make_blocks(rows):
    """rows: (block_geoid, population, bounds). Blocks are in EPSG:4269."""
    return gpd.GeoDataFrame(
        {
            "block_geoid": [r[0] for r in rows],
            "county_geoid": ["53033"] * len(rows),
            "population": [r[1] for r in rows],
        },
        geometry=[box(*r[2]) for r in rows],
        crs="EPSG:4269",
    )


def build(blocks):
    window = window_cells(tuple(blocks.total_bounds), TRANSFORM, 4, 4, CRW.fishnet_margin_cells)
    fishnet = build_fishnet(TRANSFORM, 4, window, "EPSG:4269")
    table, block_qc, slivers = build_crosswalk(blocks, fishnet, CRW)
    return fishnet, table, block_qc, slivers


def test_split_blocks_get_unit_weights_and_full_coverage():
    blocks = make_blocks([
        ("A", 100, (-120.0, 47.0, -119.98, 47.01)),  # spans two cells
        ("B", 50, (-119.98, 47.02, -119.96, 47.03)),  # spans two cells
    ])
    fishnet, table, block_qc, _ = build(blocks)

    assert fishnet["cell_id"].is_unique
    assert 13 in set(fishnet["cell_id"])  # row 3, col 0 on the full 4 x 4 grid: 3 * 4 + 0 + 1
    assert table.groupby("block_geoid")["area_weight"].sum().round(9).eq(1).all()
    assert table["block_coverage"].sub(1).abs().max() < 1e-6
    summary = check_crosswalk(fishnet, table, block_qc, CRW.weight_tol, CRW.low_coverage_threshold)
    assert summary["population_total"] == 150


def test_low_coverage_and_sliver_are_reported_not_failed():
    blocks = make_blocks([
        ("A", 100, (-120.0, 47.0, -119.98, 47.01)),
        ("C", 20, (-120.02, 47.0, -119.99, 47.01)),  # about one third inside the grid
        ("D", 0, (-119.96, 47.0, -119.95, 47.01)),  # touches the east edge: zero-area overlap
    ])
    fishnet, table, block_qc, slivers = build(blocks)

    summary = check_crosswalk(fishnet, table, block_qc, CRW.weight_tol, CRW.low_coverage_threshold)
    low = {block["block_geoid"] for block in summary["low_coverage_blocks"]}
    assert low == {"C", "D"}
    assert slivers["slivers_removed"] >= 1


def test_populated_block_without_cells_fails_the_check():
    blocks = make_blocks([
        ("A", 100, (-120.0, 47.0, -119.98, 47.01)),
        ("E", 25, (-119.96, 47.0, -119.95, 47.01)),  # populated, but only touches the grid
    ])
    fishnet, table, block_qc, _ = build(blocks)

    with pytest.raises(ValueError, match="populated blocks have no crosswalk rows"):
        check_crosswalk(fishnet, table, block_qc, CRW.weight_tol, CRW.low_coverage_threshold)
