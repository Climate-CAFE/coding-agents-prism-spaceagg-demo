"""Inspect daily PRISM GeoTIFFs inside Feature 1 ZIPs and compare each with the reference grid."""

import logging
import sys
import zipfile
from pathlib import Path

import hydra
from omegaconf import DictConfig
from rasterio.errors import RasterioError

# Reuse the raster-processing Skill's inspection and grid functions instead of copying them.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "skills" / "raster-processing" / "scripts"))
from inspect_raster import inspect_raster, validate_same_grid  # noqa: E402

from download_prism import expected_dates  # noqa: E402
from qc import check_nodata, check_reference_metadata, check_rotation, write_csv_atomic  # noqa: E402

logger = logging.getLogger(__name__)

FIELDS = ["date", "file", "issues", "matches_reference", "crs", "width", "height", "nodata"]


def read_record(zip_path: Path) -> tuple[dict | None, str | None]:
    """Inspect the GeoTIFF inside a ZIP in place. Return (record, None) or (None, problem code)."""
    if not zip_path.exists():
        return None, "missing_file"
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [name for name in archive.namelist() if name.endswith(".tif")]
        if len(members) != 1:
            return None, "unreadable"
        return inspect_raster(f"/vsizip/{zip_path}/{members[0]}"), None
    except (RasterioError, zipfile.BadZipFile, OSError):
        return None, "unreadable"


def validate_row(day, zip_path: Path, record: dict | None, problem: str | None, reference: dict | None, reference_ok: bool, tol: float) -> dict:
    """Return the validation row for one date."""
    row = {"date": day.isoformat(), "file": zip_path.name, "issues": "", "matches_reference": "",
           "crs": "", "width": "", "height": "", "nodata": ""}
    if record is not None:
        row.update(crs=record["crs"], width=record["width"], height=record["height"], nodata=record["nodata"])

    issues = [problem] if problem else []
    if not reference_ok:
        issues.append("invalid_reference_metadata")
    elif record is not None:
        # Skill grid check: CRS, shape, transform. Its NoData result is replaced by check_nodata.
        grid = [i for i in validate_same_grid(reference, record, tol) if not i.startswith("nodata")]
        issues += grid + check_rotation(record["transform"], tol) + check_nodata(record["nodata"], reference["nodata"])
        row["matches_reference"] = "FALSE" if issues else "TRUE"
    row["issues"] = ";".join(issues)
    return row


def run_year(paths: DictConfig, prism: DictConfig, year: int) -> list[dict]:
    """Validate every expected date for one year against the first expected date, and write the CSV."""
    raw_dir = Path(paths.raw_root) / "prism" / prism.variable / str(year)
    days = expected_dates(year, prism.start_date, prism.end_date)

    reference, _ = read_record(raw_dir / f"{prism.file_prefix}{days[0]:%Y%m%d}.zip")
    reference_ok = check_reference_metadata(reference, prism.transform_tol)

    rows = []
    for day in days:
        zip_path = raw_dir / f"{prism.file_prefix}{day:%Y%m%d}.zip"
        record, problem = read_record(zip_path)
        rows.append(validate_row(day, zip_path, record, problem, reference, reference_ok, prism.transform_tol))

    metadata_dir = Path(paths.metadata_root) / "prism" / prism.variable / str(year)
    write_csv_atomic(rows, FIELDS, metadata_dir / "raster_validation.csv")
    flagged = sum(1 for row in rows if row["issues"])
    logger.info("Year %d: %d dates, %d with issues, reference ok: %s", year, len(rows), flagged, reference_ok)
    return rows


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    for year in cfg.prism.years:
        run_year(cfg.paths, cfg.prism, int(year))


if __name__ == "__main__":
    main()
