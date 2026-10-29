import datetime as dt

import geopandas as gpd
import matplotlib.image as mpimg
import pandas as pd
import pytest
from shapely.geometry import box

from qc import check_yearly
from yearly_precip import draw_map, yearly_values

DAYS = [dt.date(2024, 1, d) for d in range(1, 5)]


def make_daily(rows):
    """rows: (county_geoid, date, precip_mm). Population is constant per county."""
    frame = pd.DataFrame(rows, columns=["county_geoid", "date", "precip_mm"])
    frame["population_total"] = frame["county_geoid"].map({"53001": 1000, "53003": 500})
    return frame


def outlines(*counties):
    return gpd.GeoDataFrame({"county_geoid": list(counties)},
                            geometry=[box(i, 0, i + 1, 1) for i in range(len(counties))], crs="EPSG:4269")


def test_totals_are_sums_and_means_are_totals_over_expected_days():
    daily = make_daily([("53001", d, v) for d, v in zip(DAYS, [1.0, 2.0, 3.0, 4.0])]
                       + [("53003", d, 0.5) for d in DAYS])

    yearly = yearly_values(daily, 2024, DAYS).set_index("county_geoid")

    assert yearly.loc["53001", "precip_total_mm"] == pytest.approx(10.0)
    assert yearly.loc["53001", "precip_mean_mm"] == pytest.approx(2.5)
    assert yearly.loc["53003", "precip_total_mm"] == pytest.approx(2.0)
    assert yearly.loc["53003", "precip_mean_mm"] == pytest.approx(0.5)
    assert yearly.loc["53001", "days_observed"] == yearly.loc["53001", "days_expected"] == 4
    assert yearly.loc["53001", "population"] == 1000


def test_missing_day_or_unexpected_county_fails_the_year():
    days_missing_one = [("53001", d, 1.0) for d in DAYS] + [("53003", d, 1.0) for d in DAYS[:3]]
    daily = make_daily(days_missing_one)
    yearly = yearly_values(daily, 2024, DAYS)

    with pytest.raises(ValueError, match="missing daily observations"):
        check_yearly(yearly, daily, ["53001", "53003"], outlines("53001", "53003"), len(DAYS))

    extra = make_daily([("53001", d, 1.0) for d in DAYS] + [("53999", d, 1.0) for d in DAYS])
    extra_yearly = yearly_values(extra, 2024, DAYS)
    with pytest.raises(ValueError, match="not in Feature 2 blocks"):
        check_yearly(extra_yearly, extra, ["53001"], outlines("53001"), len(DAYS))


def test_map_writes_a_titled_png(tmp_path):
    daily = make_daily([("53001", d, 1.0) for d in DAYS] + [("53003", d, 2.0) for d in DAYS])
    yearly = yearly_values(daily, 2024, DAYS)
    path = tmp_path / "map.png"

    draw_map(outlines("53001", "53003"), yearly, path, "Washington", 2024)

    image = mpimg.imread(path)
    assert path.stat().st_size > 0
    assert image.shape[0] > 100 and image.shape[1] > 100
