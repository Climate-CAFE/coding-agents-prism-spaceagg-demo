import datetime as dt
import io
import zipfile

import pytest
import requests
from omegaconf import OmegaConf

from download_prism import expected_dates, fetch_file, process_year
from qc import check_complete, check_zip, summarize

BASE = "https://example.test/800m/"
PREFIX = "prism_ppt_us_30s_"


def zip_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("file.bil", "data")
    return buffer.getvalue()


def make_cfg(tmp_path, **overrides):
    prism = {
        "base_url": BASE,
        "variable": "ppt",
        "file_prefix": PREFIX,
        "years": [2024],
        "start_date": "2024-01-01",
        "end_date": "2024-01-03",
        "retries": 3,
        "backoff_seconds": 0,
        "pause_seconds": 0,
        "timeout_seconds": 5,
        "stability": "not available",
    }
    prism.update(overrides)
    paths = {"raw_root": str(tmp_path / "raw"), "metadata_root": str(tmp_path / "meta")}
    return OmegaConf.create({"paths": paths, "prism": prism})


def listing_html(days):
    return "\n".join(f'<a href="{PREFIX}{day}.zip">x</a>' for day in days)


def test_expected_dates_leap_year_and_clip():
    assert len(expected_dates(2024, None, None)) == 366
    assert expected_dates(2024, "2024-02-29", "2024-03-01") == [dt.date(2024, 2, 29), dt.date(2024, 3, 1)]


def test_check_zip_rejects_corrupt_file(tmp_path):
    path = tmp_path / "bad.zip"
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError):
        check_zip(path)


def test_fetch_file_retries_then_gives_up(tmp_path, requests_mock):
    url = BASE + "a.zip"
    requests_mock.get(url, status_code=500)
    with pytest.raises(RuntimeError):
        fetch_file(requests.Session(), url, tmp_path / "a.zip", make_cfg(tmp_path).prism)
    assert requests_mock.call_count == 3
    assert not (tmp_path / "a.zip.part").exists()


def test_process_year_failure_then_incremental_rerun(tmp_path, requests_mock):
    cfg = make_cfg(tmp_path)
    good = zip_bytes()
    headers = {"Content-Length": str(len(good))}
    day_url = {day: f"{BASE}ppt/daily/2024/{PREFIX}{day}.zip" for day in ["20240101", "20240102", "20240103"]}
    requests_mock.get(BASE + "ppt/daily/2024/", text=listing_html(day_url))
    requests_mock.get(day_url["20240101"], content=good, headers=headers)
    requests_mock.get(day_url["20240102"], status_code=500)
    requests_mock.get(day_url["20240103"], content=good, headers=headers)

    rows = process_year(requests.Session(), 2024, cfg.paths, cfg.prism)
    assert [row["status"] for row in rows] == ["downloaded", "failed", "downloaded"]
    with pytest.raises(RuntimeError):
        check_complete(summarize(rows))

    requests_mock.reset_mock()
    requests_mock.get(day_url["20240102"], content=good, headers=headers)
    rows = process_year(requests.Session(), 2024, cfg.paths, cfg.prism)
    assert [row["status"] for row in rows] == ["skipped", "downloaded", "skipped"]
    fetched = [request.url for request in requests_mock.request_history if request.url.endswith(".zip")]
    assert fetched == [day_url["20240102"]]


def test_process_year_marks_unlisted_days_missing(tmp_path, requests_mock):
    cfg = make_cfg(tmp_path)
    url = f"{BASE}ppt/daily/2024/{PREFIX}20240101.zip"
    requests_mock.get(BASE + "ppt/daily/2024/", text=listing_html(["20240101"]))
    requests_mock.get(url, content=zip_bytes(), headers={"Content-Length": str(len(zip_bytes()))})

    rows = process_year(requests.Session(), 2024, cfg.paths, cfg.prism)
    assert [row["status"] for row in rows] == ["downloaded", "missing", "missing"]
    assert rows[1]["error"] == "Not in remote listing"
