# Spec: PRISM 800 m daily precipitation download

## Approval

- **Status:** approved
- **Version:** draft 2 (committed in d55de3b)
- **Last changed:** 2026-10-28
- **Approved by:** project lead, via chat (D1–D8 with changes below)
- **Approved on:** 2026-10-28

## Goal

Download the original PRISM 800 m daily total precipitation (`ppt`) ZIPs for the conterminous U.S., unmodified, as the raw input for later county aggregation. Gaps or corrupt files must be visible, never silently dropped.

## Scope

**In scope**
- Download `ppt` daily ZIPs for a configurable year list and date range. Initial run: 2024 (366 files).
- Incremental reruns, validation, retries, and a per-year manifest.
- Hydra config in `conf/`; Snakemake orchestration.

**Out of scope**
- Extracting ZIPs, reading rasters, reprojection, or unit conversion.
- Temporal alignment (PRISM daily = 24 h ending 12:00 UTC) and county aggregation (later features).
- Other variables. The config keeps the variable name, but only `ppt` is validated.

## Source

`https://data.prism.oregonstate.edu/time_series/us/an/800m/ppt/daily/<year>/`, files `prism_ppt_us_30s_<YYYYMMDD>.zip` (~7.6 MB each, ~2.8 GB for 2024). PRISM publishes no checksums in the listing.

## Key decisions

| ID | Decision |
|----|----------|
| D1 | Discover files from the year's directory listing; match the pattern `prism_ppt_us_30s_<YYYYMMDD>.zip`. |
| D2 | Expected files = every calendar day in the configured range. A missing day is an error. |
| D3 | Write to `<name>.part`, validate, then rename. Skip files that already pass validation; re-download only failed or invalid files. Never overwrite a valid file. |
| D4 | Validate: server `Content-Length` equals local size; `zipfile.testzip()` passes; SHA-256 recorded. |
| D5 | Three attempts per file with exponential backoff. A file that still fails is marked `failed`, the run continues, and the process exits non-zero. |
| D6 | Raw ZIPs: `data/raw/prism/ppt/<year>/`. Manifest: `data/metadata/prism/ppt/<year>/manifest.csv`, with date, file name, URL, status, bytes, SHA-256, UTC download time, source stability (or `not available`), and error. |
| D7 | Snakemake: one rule per year. Per-file logic stays in Python. |
| D8 | Sequential downloads with a 0.5 s pause between requests. |

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | Year 2024 yields exactly 366 files, one per day, named by the pattern. | Test compares the file set to the expected date list. |
| AC2 | Every file passes D4 checks. | Validation step; report lists failures. |
| AC3 | A rerun with no changes downloads nothing and leaves file hashes unchanged. | Run twice; compare manifest and SHA-256 values. |
| AC4 | With one forced failure, other files finish, the failed file is `failed`, exit is non-zero, and a rerun fetches only that file. | Mocked-HTTP pytest, plus one manual check. |
| AC5 | Manifest has one row per expected day, SHA-256 for every valid file, and a UTC timestamp for every row. | Script checks columns and row count. |
| AC6 | URL, years, date range, paths, retries, and pause come from `conf/`, not code. | Grep of `src/` for hardcoded values. |

## Open questions

- [ ] Q1: Source stability: PRISM's listing shows no stability status. Record it when a source provides it, otherwise `not available`. Confirm this is acceptable, or name a source to check. Owner: project lead. Needed before: implementation.
- [ ] Q2: Download of ~2.8 GB is approved after implementation review. Owner: project lead. Needed before: first full download.
