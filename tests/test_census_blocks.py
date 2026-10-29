import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pytest
from omegaconf import OmegaConf
from shapely.geometry import box

from census_blocks import run

BLOCK_COLUMNS = ["state_fips", "county_geoid", "block_geoid", "population", "geometry", "vintage"]
ZIP_NAME = "tl_2020_53_tabblock20.zip"


def write_block_zip(zip_path: Path, geoids=("530330001001000", "530330001001001", "530330002001000")):
    """Write a small TIGER-style block shapefile into a ZIP at zip_path."""
    count = len(geoids)
    blocks = gpd.GeoDataFrame(
        {
            "STATEFP20": ["53"] * count,
            "COUNTYFP20": ["033", "033", "020"],
            "GEOID20": list(geoids),
            "POP20": [10, 20, 30],
        },
        geometry=[box(i, 0, i + 1, 1) for i in range(count)],
        crs="EPSG:4269",
    )
    shp_dir = zip_path.parent / "shp"
    shp_dir.mkdir(parents=True, exist_ok=True)
    blocks.to_file(shp_dir / "tl.shp")
    with zipfile.ZipFile(zip_path, "w") as archive:
        for member in shp_dir.glob("tl.*"):
            archive.write(member, member.name)


def make_cfg(tmp_path: Path, population_reference: int = 60):
    census = {
        "vintage": 2020,
        "state_fips": "53",
        "base_url": "https://example.test/",
        "filename": "tl_{vintage}_{state_fips}_tabblock20.zip",
        "expected_crs": "EPSG:4269",
        "references": {"2020": {"53": {"population": population_reference, "county_count": 2}}},
        "retries": 1,
        "backoff_seconds": 0,
        "pause_seconds": 0,
        "timeout_seconds": 5,
    }
    paths = {
        "raw_root": str(tmp_path / "raw"),
        "intermediate_root": str(tmp_path / "intermediate"),
        "metadata_root": str(tmp_path / "meta"),
    }
    return OmegaConf.create({"census": census, "paths": paths})


def stage_raw_zip(tmp_path: Path, **kwargs) -> None:
    """Place the synthetic ZIP at the raw path so the run skips the network download."""
    zip_path = tmp_path / "raw" / "census" / "2020" / "53" / ZIP_NAME
    zip_path.parent.mkdir(parents=True)
    write_block_zip(zip_path, **kwargs)


def outputs(tmp_path: Path) -> tuple[Path, Path]:
    parquet = tmp_path / "intermediate" / "census" / "2020" / "53" / "blocks.parquet"
    qc = tmp_path / "meta" / "census" / "2020" / "53" / "qc_report.json"
    return parquet, qc


def test_run_publishes_blocks_and_passing_report(tmp_path):
    stage_raw_zip(tmp_path)

    run(make_cfg(tmp_path))

    parquet, qc = outputs(tmp_path)
    blocks = gpd.read_parquet(parquet)
    assert list(blocks.columns) == BLOCK_COLUMNS
    assert len(blocks) == 3
    assert json.loads(qc.read_text())["status"] == "pass"


def test_duplicate_block_geoid_publishes_nothing(tmp_path):
    duplicate = ("530330001001000", "530330001001000", "530330002001000")
    stage_raw_zip(tmp_path, geoids=duplicate)

    with pytest.raises(ValueError, match="duplicate block_geoid"):
        run(make_cfg(tmp_path))

    parquet, qc = outputs(tmp_path)
    assert not parquet.exists()
    assert json.loads(qc.read_text())["status"] == "fail"


def test_population_reference_mismatch_publishes_nothing(tmp_path):
    stage_raw_zip(tmp_path)

    with pytest.raises(ValueError, match="does not match reference"):
        run(make_cfg(tmp_path, population_reference=999))

    parquet, _ = outputs(tmp_path)
    assert not parquet.exists()
