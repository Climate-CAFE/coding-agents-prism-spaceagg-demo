import numpy as np
import pandas as pd
import pytest

from county_precip import block_means, county_means, read_window, cell_window
from rasterio.windows import Window

WIDTH = 4
NODATA = -9999.0


def make_table():
    """Block A: cells 1 and 2 (weights 0.5 each). Block B: cell 6 (weight 1). Both in county 53033."""
    table = pd.DataFrame({
        "block_geoid": ["A", "A", "B"],
        "county_geoid": ["53033", "53033", "53033"],
        "cell_id": [1, 2, 6],
        "population": [100, 100, 300],
        "area_weight": [0.5, 0.5, 1.0],
    })
    table["row"] = (table["cell_id"] - 1) // WIDTH
    table["col"] = (table["cell_id"] - 1) % WIDTH
    table["block_index"] = pd.factorize(table["block_geoid"])[0]
    return table


def blocks_frame():
    return pd.DataFrame({"county_geoid": ["53033", "53033"], "population": [100, 300]})


def grid(values):
    """A 2 x 4 window of values covering cells 1–8 (rows 0–1, cols 0–3)."""
    return np.array(values, dtype="float64").reshape(2, WIDTH)


def test_block_and_county_means_match_hand_calculation():
    table = make_table()
    values = grid([[2.0, 4.0, 0.0, 0.0], [0.0, 6.0, 0.0, 0.0]])

    precip, coverage = block_means(table, values, 0, 0, NODATA, 2)
    county = county_means(blocks_frame(), precip)

    assert precip.tolist() == pytest.approx([3.0, 6.0])  # A = (0.5*2 + 0.5*4) / 1.0; B = 6
    assert coverage.tolist() == pytest.approx([1.0, 1.0])
    # County = (100 * 3 + 300 * 6) / 400
    assert county.loc[0, "precip_mm"] == pytest.approx(5.25)
    assert county.loc[0, "population_coverage"] == pytest.approx(1.0)


def test_nodata_cell_is_excluded_and_weights_renormalize():
    table = make_table()
    values = grid([[2.0, NODATA, 0.0, 0.0], [0.0, 6.0, 0.0, 0.0]])

    precip, coverage = block_means(table, values, 0, 0, NODATA, 2)
    county = county_means(blocks_frame(), precip)

    assert precip[0] == pytest.approx(2.0)  # only cell 1 is valid; renormalized to weight 1
    assert coverage[0] == pytest.approx(0.5)  # half of block A's area had valid data
    assert county.loc[0, "precip_mm"] == pytest.approx((100 * 2.0 + 300 * 6.0) / 400)
    assert county.loc[0, "population_coverage"] == pytest.approx(1.0)


def test_county_without_valid_blocks_is_blank_and_missing_raster_raises(tmp_path):
    table = make_table()
    values = grid([[NODATA] * 4, [NODATA] * 4])

    precip, coverage = block_means(table, values, 0, 0, NODATA, 2)
    county = county_means(blocks_frame(), precip)

    assert np.isnan(county.loc[0, "precip_mm"])
    assert county.loc[0, "population_coverage"] == 0.0

    with pytest.raises(FileNotFoundError):
        read_window(tmp_path / "missing.zip", Window(0, 0, 1, 1))
