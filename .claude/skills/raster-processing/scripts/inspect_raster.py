
"""Inspect raster metadata and check grid consistency. Requires rasterio."""

import argparse
import json
from pathlib import Path

import rasterio


def inspect_raster(path):
    with rasterio.open(path) as ds:
        return {
            "path": str(path),
            "driver": ds.driver,
            "width": ds.width,
            "height": ds.height,
            "count": ds.count,
            "dtype": ds.dtypes[0],
            "crs": ds.crs.to_string() if ds.crs else None,
            "resolution": ds.res,
            "bounds": tuple(ds.bounds),
            "transform": tuple(ds.transform)[:6],
            "nodata": ds.nodata,
        }



def validate_same_grid(reference, raster, tol=1e-9):
    """Return grid differences between two raster metadata dictionaries."""
    issues = []

    if reference["crs"] != raster["crs"]:
        issues.append("crs_mismatch")

    if (reference["width"], reference["height"]) != (
        raster["width"], raster["height"]
    ):
        issues.append("shape_mismatch")

    if any(
        abs(a - b) > tol
        for a, b in zip(reference["transform"], raster["transform"])
    ):
        issues.append("transform_mismatch")

    if reference["nodata"] != raster["nodata"]:
        issues.append("nodata_mismatch")

    return issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rasters", nargs="+", type=Path)
    parser.add_argument("--tol", type=float, default=1e-9)
    args = parser.parse_args()
    records = [inspect_raster(p) for p in args.rasters]
    for rec in records[1:]:
        rec["grid_issues"] = validate_same_grid(records[0], rec, args.tol)
    print(json.dumps(records, indent=2))
