# Status: PRISM 800 m daily precipitation download

- **Last updated:** 2026-10-28
- **Current phase:** complete (T00–T10 done)
- **Completed on:** 2026-10-28

## Approval

| Document | Status | Approved by | Approved on |
|----------|--------|-------------|-------------|
| spec.md | approved | project lead, via chat | 2026-10-28 |
| plan.md | approved | project lead, via chat | 2026-10-28 |
| tasks.md | complete | — | — |
| full 2024 download (approved as ~2.8 GB; actual 7.03 GB) | approved, including the 7.03 GB total | project lead, via chat | 2026-10-29 |
| Q1 stability wording (`not available`) and `snakemake` installed via pip | approved | project lead, via chat | 2026-10-29 |
| conda env `prism-spaceagg` | created | project lead, via chat | 2026-10-28 |

## Completed tasks

- T00: git ignore rules. Verified with `git check-ignore`.
- T01: environment and Hydra config. Verified by env build and Hydra compose.
- T02–T06: listing, fetch, validation, manifest, QC. Verified by pytest (5 passed).
- T07: Snakefile. Dry run plans one job; a failing year (scratch copy, year 1900) makes Snakemake exit 1.
- T08: tests. `pytest` 5 passed in one file.
- T09: config audit. Grep clean.
- T10: 2024 download. Run 1: 366 downloaded, 0 failed. Run 2: 366 skipped, 0 downloaded. QC completeness 1.0. Evidence: `data/metadata/prism/ppt/2024/manifest.csv`, `qc_report.csv`.

## Work in progress

None.

## Blockers

| ID | Blocker | Affects | Owner | Since |
|----|---------|---------|-------|-------|

## Deviations

- Download size is 7.03 GB, not the ~2.8 GB in the approved estimate. The estimate came from the 2024-01-01 file (7.6 MB) alone; later days are larger (about 5–35 MB each). The approval covered ~2.8 GB; the 7.03 GB total was not separately approved. Reported to the project lead after the run.
- `environment.yaml` installs `snakemake` via pip, not conda-forge. conda-forge has no osx-arm64 snakemake package. Recorded here for review; the plan did not specify the install channel.
- Date range is applied as a clip within each year (`prism.start_date` and `prism.end_date` are optional and null by default). The plan named a 2024 default range; the code uses the full calendar year unless the clip is set.

## Validation results

| ID | Status | Evidence |
|----|--------|----------|
| AC1 | passing (tests) | `test_expected_dates_leap_year_and_clip`, `test_process_year_marks_unlisted_days_missing` |
| AC2 | passing (tests and real data) | `test_check_zip_rejects_corrupt_file`; 366/366 ZIPs pass `testzip`, SHA-256 and sizes match manifest |
| AC3 | passing (real data) | run 2 skipped 366; ZIP mtime, size, inode unchanged; manifest bytes and SHA-256 unchanged |
| AC4 | passing (tests) | `test_fetch_file_retries_then_gives_up`, `test_process_year_failure_then_incremental_rerun` |
| AC5 | passing | manifest has 366 rows with SHA-256 and UTC time; `test_process_year_*` |
| AC6 | passing (grep) | T09 audit |
| D7 (T07) | passing | scratch Snakemake run exits 1 on a failed year; real run exit 0 |

## Next steps

None. Q1 wording, the pip install of `snakemake`, and the 7.03 GB total were approved on 2026-10-29.
