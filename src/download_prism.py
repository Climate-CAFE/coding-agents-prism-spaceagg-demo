"""Download daily PRISM ppt ZIPs for each configured year and write a manifest and QC report."""

import datetime as dt
import logging
import re
import time
from pathlib import Path

import hydra
import requests
from omegaconf import DictConfig

from qc import check_complete, check_size, check_zip, summarize, write_csv_atomic, write_qc_report

logger = logging.getLogger(__name__)

MANIFEST_FIELDS = [
    "date",
    "file",
    "url",
    "status",
    "bytes",
    "sha256",
    "downloaded_utc",
    "stability",
    "error",
]


def expected_dates(year: int, start: str | None, end: str | None) -> list[dt.date]:
    """Return every calendar day of the year, clipped to the optional start and end dates."""
    first = dt.date(year, 1, 1)
    last = dt.date(year, 12, 31)
    if start:
        first = max(first, dt.date.fromisoformat(start))
    if end:
        last = min(last, dt.date.fromisoformat(end))
    return [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]


def parse_listing(html: str, file_prefix: str) -> dict[dt.date, str]:
    """Map each daily ZIP name in a directory listing to its date, ignoring other files."""
    pattern = re.compile(re.escape(file_prefix) + r"(\d{8})\.zip")
    found = {}
    for match in pattern.finditer(html):
        found[dt.datetime.strptime(match.group(1), "%Y%m%d").date()] = match.group(0)
    return found


def _download_once(session: requests.Session, url: str, part: Path, dest: Path, timeout: float) -> str:
    """Stream one file to a .part file, validate it, and rename it into place."""
    with session.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        expected_size = response.headers.get("Content-Length")
        with part.open("wb") as handle:
            for block in response.iter_content(chunk_size=1 << 20):
                handle.write(block)
    check_size(part, expected_size)
    digest = check_zip(part)
    part.replace(dest)
    return digest


def fetch_file(session: requests.Session, url: str, dest: Path, prism: DictConfig) -> str:
    """Download a file with retries and backoff; return its SHA-256 or raise after the last attempt."""
    part = dest.with_name(dest.name + ".part")
    for attempt in range(1, prism.retries + 1):
        try:
            return _download_once(session, url, part, dest, prism.timeout_seconds)
        except (requests.RequestException, ValueError) as error:
            logger.warning("Attempt %d of %d failed for %s: %s", attempt, prism.retries, url, error)
            part.unlink(missing_ok=True)
            if attempt < prism.retries:
                time.sleep(prism.backoff_seconds * 2 ** (attempt - 1))
    raise RuntimeError(f"All {prism.retries} attempts failed for {url}")


def _process_day(
    session: requests.Session,
    day: dt.date,
    name: str | None,
    listing_url: str,
    raw_dir: Path,
    prism: DictConfig,
) -> dict:
    """Return the manifest row for one day, skipping valid files and downloading the rest."""
    row = {
        "date": day.isoformat(),
        "file": name or "",
        "url": "",
        "status": "missing",
        "bytes": "",
        "sha256": "",
        "downloaded_utc": "",
        "stability": prism.stability,
        "error": "",
    }
    if name is None:
        row["error"] = "Not in remote listing"
        return row

    url = listing_url + name
    dest = raw_dir / name
    row["url"] = url
    if dest.exists():
        try:
            row.update(status="skipped", bytes=dest.stat().st_size, sha256=check_zip(dest))
            return row
        except ValueError:
            logger.warning("Existing file failed validation, re-downloading: %s", dest)
            dest.unlink()

    try:
        digest = fetch_file(session, url, dest, prism)
        row.update(
            status="downloaded",
            bytes=dest.stat().st_size,
            sha256=digest,
            downloaded_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        )
    except (requests.RequestException, RuntimeError) as error:
        row.update(status="failed", error=str(error))
    time.sleep(prism.pause_seconds)
    return row


def process_year(session: requests.Session, year: int, paths: DictConfig, prism: DictConfig) -> list[dict]:
    """Download the year's expected files and return one manifest row per expected day."""
    raw_dir = Path(paths.raw_root) / "prism" / prism.variable / str(year)
    raw_dir.mkdir(parents=True, exist_ok=True)
    listing_url = f"{prism.base_url}{prism.variable}/daily/{year}/"

    listing = session.get(listing_url, timeout=prism.timeout_seconds)
    listing.raise_for_status()
    available = parse_listing(listing.text, prism.file_prefix)

    days = expected_dates(year, prism.start_date, prism.end_date)
    logger.info("Year %d: %d expected, %d listed", year, len(days), len(available))

    return [
        _process_day(session, day, available.get(day), listing_url, raw_dir, prism)
        for day in days
    ]


def run_year(session: requests.Session, year: int, paths: DictConfig, prism: DictConfig) -> None:
    """Process one year, write its manifest and QC report, then raise if any file is not valid."""
    rows = process_year(session, year, paths, prism)

    metadata_dir = Path(paths.metadata_root) / "prism" / prism.variable / str(year)
    write_csv_atomic(rows, MANIFEST_FIELDS, metadata_dir / "manifest.csv")
    summary = summarize(rows)
    write_qc_report(summary, metadata_dir / "qc_report.csv")
    logger.info("Year %d summary: %s", year, summary)
    check_complete(summary)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    session = requests.Session()
    for year in cfg.prism.years:
        run_year(session, int(year), cfg.paths, cfg.prism)


if __name__ == "__main__":
    main()
