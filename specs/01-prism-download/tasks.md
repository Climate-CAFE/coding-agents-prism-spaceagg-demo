# Tasks: PRISM 800 m daily precipitation download

Check a box only after its definition of done runs.

- [x] **T00 — Ignore data and logs.** Serves: AGENTS.md. DoD: `git check-ignore` ignores `data/` and `logs/*`, not `logs/prompts.md`. Verified 2026-10-28.
- [x] **T01 — Config and environment.** Serves: D6, AC6. DoD met 2026-10-28: `prism-spaceagg` built from `environment.yaml` (snakemake via pip, since conda-forge has no osx-arm64 build); Hydra composes `paths.raw_root` and `prism.retries`; override `prism.years=[2025]` applied.
- [x] **T02 — Listing and dates.** Serves: D1, D2. DoD met: `test_expected_dates_leap_year_and_clip`; listing filter covered indirectly by `test_process_year_*`.
- [x] **T03 — Fetch.** Serves: D3, D5, D8. DoD met: `test_fetch_file_retries_then_gives_up` (3 attempts, `.part` removed); `test_process_year_failure_then_incremental_rerun` (valid files skipped, failed file alone re-fetched). Retry-then-success is not separately tested.
- [x] **T04 — Validation.** Serves: D4, AC2. DoD met: `qc.check_zip` rejects corrupt ZIPs (`test_check_zip_rejects_corrupt_file`); `qc.check_size` runs in `_download_once`.
- [x] **T05 — Manifest.** Serves: D6, AC5. DoD met: `write_csv_atomic` writes one row per expected day with UTC time and `stability`; checked by `test_process_year_*`.
- [x] **T06 — QC.** Serves: D2, AC5. DoD met: `qc.summarize`, `qc.check_complete` exercised in `test_process_year_failure_then_incremental_rerun`; unlisted days in `test_process_year_marks_unlisted_days_missing`.
- [x] **T07 — Snakefile.** Serves: D7. DoD met 2026-10-28: `snakemake -n` lists one `download_prism_ppt` job for 2024; in a scratch copy with year 1900, Snakemake exits 1 on the failed job.
- [x] **T08 — Tests.** Serves: AC1, AC4, AC5. DoD met: `pytest` 5 passed in `prism-spaceagg`, after trimming to one test file.
- [x] **T09 — Config audit.** Serves: AC6. DoD met: grep of `src/` and `Snakefile` finds no URL, year, variable, or scientific number outside `conf/`. Only file names and the rule name match.
- [x] **T10 — Real 2024 run.** Depends: T07, implementation review, download approval (spec Q2). Serves: AC2, AC3. DoD met 2026-10-28: 366 valid files, completeness 1.0; independent check: all ZIPs pass `testzip`, SHA-256 and sizes match manifest; rerun skipped 366, ZIP mtime/size/inode unchanged, manifest bytes and SHA-256 unchanged.
