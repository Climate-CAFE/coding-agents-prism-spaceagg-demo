"""Quality control checks and reports, organized by feature.

Shared helpers come first. Each feature adds its own section below.
"""

import csv
import hashlib
import json
import logging
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Shared helpers


def write_csv_atomic(rows: list[dict], fieldnames: list[str], path: Path) -> None:
    """Write a CSV to a temporary file, then rename it into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


# Feature 1: PRISM daily download


def sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check_zip(path: Path) -> str:
    """Raise ValueError if the ZIP cannot be read or has a bad member; otherwise return its SHA-256."""
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
    except zipfile.BadZipFile as error:
        raise ValueError(f"Not a readable ZIP: {path.name}") from error
    if bad_member is not None:
        raise ValueError(f"Corrupt member {bad_member} in {path.name}")
    return sha256(path)


def check_size(path: Path, expected: str | None) -> None:
    """Raise ValueError if the file size does not match the server's Content-Length header."""
    if expected is None:
        raise ValueError(f"No Content-Length to check {path.name} against")
    actual = path.stat().st_size
    if actual != int(expected):
        raise ValueError(f"Size {actual} of {path.name} does not match Content-Length {expected}")


def check_file_set(expected: set, present: set) -> tuple[list, list]:
    """Return the expected items that are absent and the present items that were not expected."""
    return sorted(expected - present), sorted(present - expected)


def summarize(rows: list[dict]) -> dict:
    """Count rows by status. Each row is one expected file; only downloaded or skipped rows are valid."""
    counts = {"expected": len(rows), "downloaded": 0, "skipped": 0, "failed": 0, "missing": 0}
    for row in rows:
        counts[row["status"]] += 1
    counts["valid"] = counts["downloaded"] + counts["skipped"]
    counts["completeness"] = counts["valid"] / counts["expected"] if rows else 0.0
    return counts


def check_complete(summary: dict) -> None:
    """Raise if there are no expected files or any expected file is not valid."""
    if summary["expected"] == 0:
        raise RuntimeError("No files were expected; check the date range and years.")
    if summary["valid"] != summary["expected"]:
        raise RuntimeError(f"Incomplete download: {summary}")


def write_qc_report(summary: dict, path: Path) -> None:
    """Write the summary as a metric and value CSV."""
    rows = [{"metric": metric, "value": value} for metric, value in summary.items()]
    write_csv_atomic(rows, ["metric", "value"], path)


# Feature 2: Census blocks

BLOCK_COLUMNS = ["state_fips", "county_geoid", "block_geoid", "population", "geometry", "vintage"]


def check_essential(blocks, expected_crs: str) -> dict:
    """Raise ValueError if any essential block check fails; otherwise return the observed results."""
    missing = [column for column in BLOCK_COLUMNS if column not in blocks.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    failures = []
    duplicates = int(blocks["block_geoid"].duplicated().sum())
    if duplicates:
        failures.append(f"{duplicates} duplicate block_geoid values")
    if not pd.api.types.is_integer_dtype(blocks["population"]):
        failures.append("population is not an integer type")
    nulls = int(blocks["population"].isna().sum())
    if nulls:
        failures.append(f"{nulls} null population values")
    negatives = int((blocks["population"] < 0).sum())
    if negatives:
        failures.append(f"{negatives} negative population values")
    invalid = int((~blocks.geometry.is_valid).sum())
    if invalid:
        failures.append(f"{invalid} invalid geometries")
    if blocks.crs is None or not blocks.crs.equals(expected_crs):
        failures.append(f"CRS {blocks.crs} does not match expected {expected_crs}")
    if failures:
        raise ValueError("; ".join(failures))

    return {
        "rows": len(blocks),
        "crs": blocks.crs.to_string(),
        "population_total": int(blocks["population"].sum()),
        "county_count": int(blocks["county_geoid"].nunique()),
    }


def check_reference(observed: dict, reference: dict | None) -> dict:
    """Compare population and county count with configured references; skip any that are not set."""
    reference = reference or {}
    results = {}
    comparisons = {"population": "population_total", "county_count": "county_count"}
    for name, observed_key in comparisons.items():
        expected = reference.get(name)
        if expected is None:
            logger.warning("No reference %s configured; skipping that check", name)
            results[name] = {"status": "skipped"}
            continue
        status = "pass" if observed[observed_key] == expected else "fail"
        results[name] = {"status": status, "expected": expected, "observed": observed[observed_key]}
        if status == "fail":
            raise ValueError(f"{name} {observed[observed_key]} does not match reference {expected}")
    return results


def write_json_atomic(report: dict, path: Path) -> None:
    """Write a JSON report to a temporary file, then rename it into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=2) + "\n")
    tmp.replace(path)


# Feature 3: PRISM rasters


def check_rotation(transform: tuple, tol: float) -> list[str]:
    """Flag a rotated or skewed affine transform (non-zero b or d terms)."""
    b, d = transform[1], transform[3]
    return ["rotated_transform"] if abs(b) > tol or abs(d) > tol else []


def check_nodata(nodata, reference_nodata) -> list[str]:
    """Flag a missing NoData value or one that differs from the reference NoData."""
    if nodata is None:
        return ["nodata_missing"]
    if nodata != reference_nodata:
        return ["nodata_mismatch"]
    return []


def check_reference_metadata(reference: dict | None, tol: float) -> bool:
    """Return True when the reference raster is readable, unrotated, and has a NoData value."""
    return reference is not None and not check_rotation(reference["transform"], tol) and reference["nodata"] is not None


# Feature 4: block–cell crosswalk


def check_crosswalk(fishnet, crosswalk, blocks, weight_tol: float, low_threshold: float) -> dict:
    """Raise ValueError on essential failures; otherwise return counts and low-coverage warnings."""
    failures = []
    duplicate_cells = int(fishnet["cell_id"].duplicated().sum())
    if duplicate_cells:
        failures.append(f"{duplicate_cells} duplicate cell_id values")
    duplicate_pairs = int(crosswalk.duplicated(["block_geoid", "cell_id"]).sum())
    if duplicate_pairs:
        failures.append(f"{duplicate_pairs} duplicate block–cell pairs")
    weight_sums = crosswalk.groupby("block_geoid")["area_weight"].sum()
    bad_weights = int((abs(weight_sums - 1.0) > weight_tol).sum())
    if bad_weights:
        failures.append(f"{bad_weights} blocks whose weights do not sum to 1")
    populated = blocks[blocks["population"] > 0]
    missing = int((~populated["block_geoid"].isin(crosswalk["block_geoid"])).sum())
    if missing:
        failures.append(f"{missing} populated blocks have no crosswalk rows")
    population_total = int(blocks["population"].sum())
    crosswalk_population = int(crosswalk.drop_duplicates("block_geoid")["population"].sum())
    if crosswalk_population != population_total:
        failures.append(f"crosswalk population {crosswalk_population} does not match block total {population_total}")
    if failures:
        raise ValueError("; ".join(failures))

    low = blocks[blocks["coverage"] < low_threshold]
    if len(low):
        logger.warning("%d blocks below %.2f coverage", len(low), low_threshold)
    return {
        "fishnet_cells": len(fishnet),
        "crosswalk_rows": len(crosswalk),
        "blocks": len(blocks),
        "population_total": population_total,
        "low_coverage_threshold": low_threshold,
        "low_coverage_blocks": [{"block_geoid": g, "coverage": c} for g, c in zip(low["block_geoid"], low["coverage"])],
    }


# Feature 5: county daily precipitation


def check_county_daily(frame: pd.DataFrame, expected_dates: list, counties: list) -> dict:
    """Raise ValueError on essential failures; otherwise return counts and coverage summaries."""
    failures = []
    values = frame["precip_mm"].dropna()
    if not np.isfinite(values).all() or (values < 0).any():
        failures.append("precipitation values must be finite and non-negative")
    duplicates = int(frame.duplicated(["county_geoid", "date"]).sum())
    if duplicates:
        failures.append(f"{duplicates} duplicate county–date rows")
    expected_rows = len(expected_dates) * len(counties)
    if len(frame) != expected_rows:
        failures.append(f"{len(frame)} rows, expected {expected_rows}")
    if set(frame["date"]) != set(expected_dates):
        failures.append("dates do not match the expected dates")
    per_date = frame.groupby("date")["county_geoid"].nunique()
    if (per_date != len(counties)).any():
        failures.append("some dates do not include every county")
    if failures:
        raise ValueError("; ".join(failures))
    return {
        "expected_rows": expected_rows,
        "rows": len(frame),
        "dates": len(expected_dates),
        "counties": len(counties),
        "rows_with_precip": int(frame["precip_mm"].notna().sum()),
        "precip_min_mm": float(values.min()),
        "precip_max_mm": float(values.max()),
        "population_coverage_min": float(frame["population_coverage"].min()),
        "population_coverage_mean": float(frame["population_coverage"].mean()),
    }


# Feature 6: yearly county precipitation


def check_yearly(yearly: pd.DataFrame, daily: pd.DataFrame, block_counties: list, outlines, days_expected: int) -> dict:
    """Raise ValueError on essential failures; otherwise return counts and value ranges."""
    failures = []
    output_counties = set(yearly["county_geoid"])
    expected_counties = set(block_counties)
    missing = sorted(expected_counties - output_counties)
    unexpected = sorted(output_counties - expected_counties)
    if missing:
        failures.append(f"{len(missing)} counties in Feature 2 blocks are missing from the output: {missing[:5]}")
    if unexpected:
        failures.append(f"{len(unexpected)} counties in the output are not in Feature 2 blocks: {unexpected[:5]}")
    if yearly["county_geoid"].duplicated().any():
        failures.append("duplicate county rows in the yearly output")
    outline_counties = set(outlines["county_geoid"])
    if outline_counties != expected_counties:
        failures.append("county outlines do not match the Feature 2 block county set")
    if not outlines.geometry.is_valid.all():
        failures.append("invalid county outline geometry")

    incomplete = int((yearly["days_observed"] != yearly["days_expected"]).sum())
    if incomplete:
        failures.append(f"{incomplete} counties have missing daily observations")
    totals = yearly["precip_total_mm"]
    means = yearly["precip_mean_mm"]
    if not np.isfinite(totals).all() or (totals < 0).any() or not np.isfinite(means).all():
        failures.append("yearly totals and means must be finite and non-negative")
    if not np.allclose(means * days_expected, totals, rtol=0, atol=1e-9):
        failures.append("precip_mean_mm times days_expected does not equal precip_total_mm")
    if (daily.groupby("county_geoid")["population_total"].nunique() > 1).any():
        failures.append("county population varies across days")
    if failures:
        raise ValueError("; ".join(failures))
    return {
        "counties": len(yearly),
        "days_expected": days_expected,
        "population_total": int(yearly["population"].sum()),
        "precip_total_min_mm": float(totals.min()),
        "precip_total_max_mm": float(totals.max()),
        "precip_mean_min_mm_per_day": float(means.min()),
        "precip_mean_max_mm_per_day": float(means.max()),
    }

