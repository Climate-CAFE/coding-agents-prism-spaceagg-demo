import zipfile
from pathlib import Path

import numpy as np
import rasterio
from omegaconf import OmegaConf
from rasterio.transform import Affine

from validate_rasters import run_year

PREFIX = "prism_ppt_us_30s_"
GOOD = Affine(0.5, 0, 0, 0, -0.5, 0)


def write_zip(raw_dir: Path, scratch: Path, day: str, transform=GOOD, width=4, nodata=-9999, garbage=False):
    """Write one date's ZIP containing a GeoTIFF, or a non-TIFF file named .tif when garbage is True."""
    name = f"{PREFIX}{day}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    tif = scratch / f"{name}.tif"
    if garbage:
        tif.write_bytes(b"not a tiff")
    else:
        with rasterio.open(
            tif, "w", driver="GTiff", width=width, height=3, count=1, dtype="float32",
            crs="EPSG:4269", transform=transform, nodata=nodata,
        ) as ds:
            ds.write(np.zeros((1, 3, width), dtype="float32"))
    with zipfile.ZipFile(raw_dir / f"{name}.zip", "w") as archive:
        archive.write(tif, arcname=tif.name)


def make_cfg(tmp_path: Path, end_date: str):
    prism = {
        "variable": "ppt",
        "file_prefix": PREFIX,
        "start_date": "2024-01-01",
        "end_date": end_date,
        "transform_tol": 1.0e-9,
    }
    paths = {"raw_root": str(tmp_path / "raw"), "metadata_root": str(tmp_path / "meta")}
    return OmegaConf.create({"paths": paths, "prism": prism})


def test_matching_grid_gives_true_for_every_date(tmp_path):
    raw = tmp_path / "raw" / "prism" / "ppt" / "2024"
    write_zip(raw, tmp_path, "20240101")
    write_zip(raw, tmp_path, "20240102")
    cfg = make_cfg(tmp_path, "2024-01-02")

    rows = run_year(cfg.paths, cfg.prism, 2024)

    assert [row["matches_reference"] for row in rows] == ["TRUE", "TRUE"]
    assert all(row["issues"] == "" for row in rows)
    assert (tmp_path / "meta" / "prism" / "ppt" / "2024" / "raster_validation.csv").exists()


def test_each_problem_gets_its_issue_code(tmp_path):
    raw = tmp_path / "raw" / "prism" / "ppt" / "2024"
    write_zip(raw, tmp_path, "20240101")  # reference
    # 20240102 has no ZIP at all: missing_file
    write_zip(raw, tmp_path, "20240103", garbage=True)  # unreadable
    write_zip(raw, tmp_path, "20240104", width=5)  # shape_mismatch
    write_zip(raw, tmp_path, "20240105", nodata=-1)  # nodata_mismatch
    write_zip(raw, tmp_path, "20240106", nodata=None)  # nodata_missing
    write_zip(raw, tmp_path, "20240107", transform=Affine(0.25, 0, 0, 0, -0.5, 0))  # transform_mismatch
    cfg = make_cfg(tmp_path, "2024-01-07")

    rows = {row["date"]: row for row in run_year(cfg.paths, cfg.prism, 2024)}

    assert rows["2024-01-01"]["matches_reference"] == "TRUE"
    assert rows["2024-01-02"]["issues"] == "missing_file"
    assert rows["2024-01-03"]["issues"] == "unreadable"
    assert rows["2024-01-04"]["issues"] == "shape_mismatch"
    assert rows["2024-01-05"]["issues"] == "nodata_mismatch"
    assert rows["2024-01-06"]["issues"] == "nodata_missing"
    assert rows["2024-01-07"]["issues"] == "transform_mismatch"
    assert rows["2024-01-02"]["matches_reference"] == ""
    assert rows["2024-01-04"]["matches_reference"] == "FALSE"


def test_rotated_reference_makes_every_row_invalid(tmp_path):
    raw = tmp_path / "raw" / "prism" / "ppt" / "2024"
    write_zip(raw, tmp_path, "20240101", transform=Affine(0.5, 0.1, 0, 0.1, -0.5, 0))  # rotated reference
    write_zip(raw, tmp_path, "20240102")
    cfg = make_cfg(tmp_path, "2024-01-02")

    rows = run_year(cfg.paths, cfg.prism, 2024)

    assert all(row["issues"] == "invalid_reference_metadata" for row in rows)
    assert all(row["matches_reference"] == "" for row in rows)
