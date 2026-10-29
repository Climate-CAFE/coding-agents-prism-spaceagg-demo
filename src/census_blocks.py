"""Download TIGER/Line census blocks for one vintage and state and publish a cleaned GeoParquet."""

import logging
from pathlib import Path

import geopandas as gpd
import hydra
import requests
from omegaconf import DictConfig

from download_prism import fetch_file
from qc import check_essential, check_reference, check_zip, sha256, write_json_atomic

logger = logging.getLogger(__name__)


def state_key(state_fips) -> str:
    """Return the state FIPS as a two-digit string, since Hydra overrides parse it as an integer."""
    return str(state_fips).zfill(2)


def fetch_raw_zip(census: DictConfig, zip_path: Path) -> None:
    """Download the block ZIP unless a valid copy already exists."""
    if zip_path.exists():
        try:
            check_zip(zip_path)
            logger.info("Raw ZIP already valid, skipping download: %s", zip_path)
            return
        except ValueError:
            logger.warning("Existing ZIP failed validation, re-downloading: %s", zip_path)
            zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    url = census.base_url + zip_path.name
    fetch_file(requests.Session(), url, zip_path, census)


def build_blocks(zip_path: Path, vintage: int) -> gpd.GeoDataFrame:
    """Read the block shapefile from the ZIP and keep the required columns under their cleaned names."""
    raw = gpd.read_file(f"zip://{zip_path}")
    return gpd.GeoDataFrame(
        {
            "state_fips": raw["STATEFP20"],
            "county_geoid": raw["STATEFP20"] + raw["COUNTYFP20"],
            "block_geoid": raw["GEOID20"],
            "population": raw["POP20"],
            "geometry": raw.geometry,
            "vintage": vintage,
        },
        geometry="geometry",
        crs=raw.crs,
    )


def run(cfg: DictConfig) -> None:
    """Run download, transform, QC, and publish for the configured vintage and state."""
    census = cfg.census
    vintage = int(census.vintage)
    state = state_key(census.state_fips)
    filename = census.filename.format(vintage=vintage, state_fips=state)

    zip_path = Path(cfg.paths.raw_root) / "census" / str(vintage) / state / filename
    out_dir = Path(cfg.paths.intermediate_root) / "census" / str(vintage) / state
    qc_path = Path(cfg.paths.metadata_root) / "census" / str(vintage) / state / "qc_report.json"
    report = {"vintage": vintage, "state_fips": state, "source_file": filename, "source_sha256": None}

    fetch_raw_zip(census, zip_path)
    report["source_sha256"] = sha256(zip_path)

    blocks = build_blocks(zip_path, vintage)
    try:
        observed = check_essential(blocks, census.expected_crs)
        reference = census.references.get(str(vintage), {}).get(state)
        checks = check_reference(observed, reference)
    except ValueError as error:
        write_json_atomic({**report, "status": "fail", "error": str(error)}, qc_path)
        raise

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "blocks.parquet.tmp"
    blocks.to_parquet(tmp)
    tmp.replace(out_dir / "blocks.parquet")
    write_json_atomic({**report, "status": "pass", "essential": observed, "reference": checks}, qc_path)
    logger.info("Published %d blocks to %s", observed["rows"], out_dir / "blocks.parquet")


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    run(cfg)


if __name__ == "__main__":
    main()
