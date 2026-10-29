import hashlib
import json
import re
from pathlib import Path

import yaml

PRISM = yaml.safe_load(Path("conf/prism_ppt.yaml").read_text())["prism"]
CENSUS = yaml.safe_load(Path("conf/census.yaml").read_text())["census"]
PATHS = yaml.safe_load(Path("conf/datapaths.yaml").read_text())["paths"]

METADATA_DIR = f"{PATHS['metadata_root']}/prism/{PRISM['variable']}/{{year}}"
CENSUS_DIR = "{vintage}/{state_fips}"
CENSUS_TARGETS = [(str(t["vintage"]), str(t["state_fips"]).zfill(2)) for t in CENSUS["targets"]]
REFERENCE_YEAR = PRISM["years"][0]
CROSSWALK = yaml.safe_load(Path("conf/crosswalk.yaml").read_text())["crosswalk"]


def qc_sections(features=()):
    """Shared QC helpers plus the named feature sections of src/qc.py, so a rule rebuilds only for its own QC code."""
    chunks = re.split(r"(?m)^(?=# Feature \d+: )", Path("src/qc.py").read_text())
    selected = [c for c in chunks[1:] if any(c.startswith(f"# Feature {f}:") for f in features)]
    return chunks[0] + "".join(selected)


def content_hash(*paths, qc_features=()):
    """Hash file contents so code or config edits trigger a rebuild; timestamps alone do not."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(Path(path).read_bytes())
    digest.update(qc_sections(qc_features).encode())
    return digest.hexdigest()



rule all:
    input:
        expand(f"{METADATA_DIR}/qc_report.csv", year=PRISM["years"]),
        expand(f"{PATHS['intermediate_root']}/census/{CENSUS_DIR}/blocks.parquet", zip,
               vintage=[v for v, _ in CENSUS_TARGETS], state_fips=[s for _, s in CENSUS_TARGETS]),
        expand(f"{METADATA_DIR}/raster_validation.csv", year=PRISM["years"]),
        expand(f"{PATHS['metadata_root']}/crosswalk/{CENSUS_DIR}/qc_report.json", zip,
               vintage=[v for v, _ in CENSUS_TARGETS], state_fips=[s for _, s in CENSUS_TARGETS]),
        expand(f"{PATHS['output_root']}/prism_county_daily/{CENSUS_DIR}/county_daily_{{year}}.parquet",
               vintage=[v for v, _ in CENSUS_TARGETS for _ in PRISM["years"]],
               state_fips=[s for _, s in CENSUS_TARGETS for _ in PRISM["years"]],
               year=[y for _ in CENSUS_TARGETS for y in PRISM["years"]]),
        expand(f"{PATHS['output_root']}/prism_county_yearly/{CENSUS_DIR}/county_yearly_{{year}}.parquet",
               vintage=[v for v, _ in CENSUS_TARGETS for _ in PRISM["years"]],
               state_fips=[s for _, s in CENSUS_TARGETS for _ in PRISM["years"]],
               year=[y for _ in CENSUS_TARGETS for y in PRISM["years"]]),
        expand(f"{PATHS['output_root']}/figures/{CENSUS_DIR}/county_mean_daily_precip_{{year}}.png", zip,
               vintage=[v for v, _ in CENSUS_TARGETS for _ in PRISM["years"]],
               state_fips=[s for _, s in CENSUS_TARGETS for _ in PRISM["years"]],
               year=[y for _ in CENSUS_TARGETS for y in PRISM["years"]]),


rule download_prism_ppt:
    output:
        manifest=f"{METADATA_DIR}/manifest.csv",
        qc=f"{METADATA_DIR}/qc_report.csv",
    log:
        f"{PATHS['log_dir']}/download_prism_ppt_{{year}}.log",
    wildcard_constraints:
        year=r"\d{4}",
    shell:
        "python src/download_prism.py prism.years=[{wildcards.year}] > {log} 2>&1"


rule validate_prism_rasters:
    input:
        manifest=f"{METADATA_DIR}/manifest.csv",
    output:
        report=f"{METADATA_DIR}/raster_validation.csv",
    log:
        f"{PATHS['log_dir']}/validate_prism_rasters_{{year}}.log",
    wildcard_constraints:
        year=r"\d{4}",
    shell:
        "python src/validate_rasters.py prism.years=[{wildcards.year}] > {log} 2>&1"


rule census_blocks:
    input:
        script="src/census_blocks.py",
    output:
        raw=f"{PATHS['raw_root']}/census/{CENSUS_DIR}/{CENSUS['filename']}",
        blocks=f"{PATHS['intermediate_root']}/census/{CENSUS_DIR}/blocks.parquet",
        qc=f"{PATHS['metadata_root']}/census/{CENSUS_DIR}/qc_report.json",
    log:
        f"{PATHS['log_dir']}/census_blocks_{{vintage}}_{{state_fips}}.log",
    wildcard_constraints:
        vintage=r"\d{4}",
        state_fips=r"\d{2}",
    shell:
        "python src/census_blocks.py census.vintage={wildcards.vintage} "
        "census.state_fips={wildcards.state_fips} > {log} 2>&1"


rule build_crosswalk:
    input:
        blocks=f"{PATHS['intermediate_root']}/census/{CENSUS_DIR}/blocks.parquet",
        validation=f"{PATHS['metadata_root']}/prism/{PRISM['variable']}/{REFERENCE_YEAR}/raster_validation.csv",
        configs=["conf/crosswalk.yaml", "conf/census.yaml", "conf/prism_ppt.yaml"],
        code=["src/crosswalk.py"],
    output:
        fishnet=f"{PATHS['intermediate_root']}/crosswalk/{CENSUS_DIR}/fishnet.parquet",
        crosswalk=f"{PATHS['intermediate_root']}/crosswalk/{CENSUS_DIR}/block_cell_crosswalk.parquet",
        qc=f"{PATHS['metadata_root']}/crosswalk/{CENSUS_DIR}/qc_report.json",
    params:
        crosswalk=json.dumps(CROSSWALK, sort_keys=True),
        content=content_hash("src/crosswalk.py", "conf/crosswalk.yaml", "conf/census.yaml", "conf/prism_ppt.yaml",
                             qc_features=(3, 4)),
    log:
        f"{PATHS['log_dir']}/build_crosswalk_{{vintage}}_{{state_fips}}.log",
    wildcard_constraints:
        vintage=r"\d{4}",
        state_fips=r"\d{2}",
    shell:
        "python src/crosswalk.py census.vintage={wildcards.vintage} "
        "census.state_fips={wildcards.state_fips} > {log} 2>&1"


rule aggregate_county_daily:
    input:
        crosswalk=f"{PATHS['intermediate_root']}/crosswalk/{CENSUS_DIR}/block_cell_crosswalk.parquet",
        crosswalk_qc=f"{PATHS['metadata_root']}/crosswalk/{CENSUS_DIR}/qc_report.json",
        validation=f"{PATHS['metadata_root']}/prism/{PRISM['variable']}/{{year}}/raster_validation.csv",
        manifest=f"{PATHS['metadata_root']}/prism/{PRISM['variable']}/{{year}}/manifest.csv",
        configs=["conf/crosswalk.yaml", "conf/census.yaml", "conf/prism_ppt.yaml"],
        code=["src/county_precip.py", "src/crosswalk.py"],
    output:
        out=f"{PATHS['output_root']}/prism_county_daily/{CENSUS_DIR}/county_daily_{{year}}.parquet",
        qc=f"{PATHS['metadata_root']}/prism_county_daily/{CENSUS_DIR}/county_daily_{{year}}_qc.json",
    params:
        content=content_hash("src/county_precip.py", "src/crosswalk.py",
                             "conf/crosswalk.yaml", "conf/census.yaml", "conf/prism_ppt.yaml",
                             qc_features=(3, 4, 5)),
    log:
        f"{PATHS['log_dir']}/aggregate_county_daily_{{vintage}}_{{state_fips}}_{{year}}.log",
    wildcard_constraints:
        vintage=r"\d{4}",
        state_fips=r"\d{2}",
        year=r"\d{4}",
    shell:
        "python src/county_precip.py +year={wildcards.year} census.vintage={wildcards.vintage} "
        "census.state_fips={wildcards.state_fips} > {log} 2>&1"


rule yearly_county_precip:
    input:
        daily=f"{PATHS['output_root']}/prism_county_daily/{CENSUS_DIR}/county_daily_{{year}}.parquet",
        daily_qc=f"{PATHS['metadata_root']}/prism_county_daily/{CENSUS_DIR}/county_daily_{{year}}_qc.json",
        blocks=f"{PATHS['intermediate_root']}/census/{CENSUS_DIR}/blocks.parquet",
        raw=f"{PATHS['raw_root']}/census/{CENSUS_DIR}/{CENSUS['filename']}",
        configs=["conf/census.yaml", "conf/prism_ppt.yaml"],
        code=["src/yearly_precip.py", "src/county_precip.py"],
    output:
        out=f"{PATHS['output_root']}/prism_county_yearly/{CENSUS_DIR}/county_yearly_{{year}}.parquet",
        qc=f"{PATHS['metadata_root']}/prism_county_yearly/{CENSUS_DIR}/county_yearly_{{year}}_qc.json",
        figure=f"{PATHS['output_root']}/figures/{CENSUS_DIR}/county_mean_daily_precip_{{year}}.png",
    params:
        content=content_hash("src/yearly_precip.py", "src/county_precip.py", "src/crosswalk.py",
                             "conf/census.yaml", "conf/prism_ppt.yaml",
                             qc_features=(3, 4, 5, 6)),
    log:
        f"{PATHS['log_dir']}/yearly_county_precip_{{vintage}}_{{state_fips}}_{{year}}.log",
    wildcard_constraints:
        vintage=r"\d{4}",
        state_fips=r"\d{2}",
        year=r"\d{4}",
    shell:
        "python src/yearly_precip.py +year={wildcards.year} census.vintage={wildcards.vintage} "
        "census.state_fips={wildcards.state_fips} > {log} 2>&1"

