# Plan: PRISM 800 m daily precipitation download

- **Spec:** `specs/01-prism-download/spec.md` (draft 2, approved 2026-10-28)
- **Status:** approved 2026-10-28

## Approach

One Hydra-configured script downloads a year of `ppt` ZIPs and writes its manifest. Each file goes to a `.part` file, is validated, then renamed. Files that already pass are skipped. All validation and QC live in `src/qc.py`, which the downloader calls. One root Snakefile runs each configured year.

## Layout

```
Snakefile                  # one rule per year
conf/config.yaml           # Hydra composition
conf/datapaths.yaml        # all data and log paths
conf/prism_ppt.yaml        # PRISM settings
src/download_prism.py      # listing, fetch, retries, skip, manifest
src/qc.py                  # validation and QC, sections per feature
tests/test_download_prism.py  # essential download and QC tests
environment.yaml           # prism-spaceagg
```

## Configuration

| Parameter | Value | File | Decision |
|-----------|-------|------|----------|
| Source URL | `https://data.prism.oregonstate.edu/time_series/us/an/800m/` | `prism_ppt.yaml` | D1 |
| Years, date range | `[2024]`, 2024-01-01 to 2024-12-31 | `prism_ppt.yaml` | D2 |
| Retries, backoff | 3, 2 s doubling | `prism_ppt.yaml` | D5 |
| Pause, timeout | 0.5 s, 60 s | `prism_ppt.yaml` | D8 |
| Source stability | `not available` unless an official source confirms | `prism_ppt.yaml` | Spec Q1 |
| Raw, metadata, log roots | `data/raw`, `data/metadata`, `logs` | `datapaths.yaml` | D6 |

## Traceability

| Spec item | Element | Task |
|-----------|---------|------|
| D1 | `parse_listing` | T02 |
| D2 | `expected_dates`, `qc.check_file_set` | T02, T06 |
| D3 | `fetch_file` (skip, `.part`) | T03 |
| D4 | `qc.check_zip`, `qc.check_size` | T04 |
| D5, D8 | `fetch_file` (retry, pause) | T03 |
| D6 | `run_year` (manifest), `datapaths.yaml` | T01, T05 |
| D7 | `Snakefile` | T07 |
| AC1 | `expected_dates` | T08 |
| AC2 | `qc.check_zip`, `qc.check_size`, `qc.summarize` | T04, T10 |
| AC3 | skip logic | T03, T10 |
| AC4 | retry and exit code | T03, T08 |
| AC5 | manifest write, `qc.summarize` | T05, T06, T08 |
| AC6 | `conf/` files | T09 |

## Validation

- **AC1, AC4, AC5:** pytest with mocked HTTP and pure-function QC tests.
- **AC2, AC3:** real 2024 run after implementation review.
- **AC6:** grep of `src/` and `Snakefile` for hardcoded values.

## Skills applied

- **python-pipeline-style:** structure, Hydra entry point, tests. Consult before coding.
- **snakemake-workflow:** year-level rule and failure exit.

## Data manifest

Raw ZIPs in `data/raw/prism/ppt/<year>/` (unmodified). Manifest and QC report in `data/metadata/prism/ppt/<year>/`.

## Risks

- Server rate limits or outage: retries, pause, rerun fetches only failures.
- Partial files treated as complete: `.part` rename after validation.
- Stability unknown: recorded as `not available`.

## Alternatives considered

- One Snakemake rule per day: DAG overhead with no benefit.
- Guessed filenames without listing: listing is the only source of truth for the file set.
