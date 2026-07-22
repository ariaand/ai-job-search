"""Covers the failure-detection gap found while smoke-testing live boards:
JobSpy logs board failures (403/429) through its own loggers and returns an
empty DataFrame instead of raising, so a bare try/except never sees them.
"""

from __future__ import annotations

import logging
import sys
import types

import pandas as pd
import pytest

from job_search.jobspy_client import JobSpyClient


def _install_fake_jobspy(monkeypatch, scrape_jobs_fn):
    fake_module = types.ModuleType("jobspy")
    fake_module.scrape_jobs = scrape_jobs_fn
    monkeypatch.setitem(sys.modules, "jobspy", fake_module)


def test_silent_board_failure_is_detected(monkeypatch):
    """scrape_jobs() returns an empty df without raising, but logs a
    'JobSpy:ZipRecruiter' error - this must surface as a BoardResult error,
    not a silent empty success."""

    def fake_scrape_jobs(**kwargs):
        logging.getLogger("JobSpy:ZipRecruiter").error(
            'ZipRecruiter response status code 403 with response: {"error_code":"forbidden aa"}'
        )
        return pd.DataFrame()

    _install_fake_jobspy(monkeypatch, fake_scrape_jobs)

    client = JobSpyClient(max_retries_per_site=1)
    results = client.search(sites=["zip_recruiter"], search_term="staff accountant")

    assert len(results) == 1
    assert not results[0].ok
    assert "403" in results[0].error


def test_successful_board_with_jobs_is_not_marked_failed(monkeypatch):
    def fake_scrape_jobs(**kwargs):
        return pd.DataFrame([{"title": "Staff Accountant", "company": "Acme", "location": "Remote"}])

    _install_fake_jobspy(monkeypatch, fake_scrape_jobs)

    client = JobSpyClient(max_retries_per_site=1)
    results = client.search(sites=["indeed"], search_term="staff accountant")

    assert results[0].ok
    assert len(results[0].jobs) == 1


def test_empty_result_without_logged_errors_is_a_legitimate_success(monkeypatch):
    """An empty df with no board-specific error logged means the board
    genuinely had no matches - not a failure."""

    def fake_scrape_jobs(**kwargs):
        return pd.DataFrame()

    _install_fake_jobspy(monkeypatch, fake_scrape_jobs)

    client = JobSpyClient(max_retries_per_site=1)
    results = client.search(sites=["indeed"], search_term="staff accountant")

    assert results[0].ok
    assert results[0].jobs == []


def test_unrelated_logger_noise_does_not_mark_board_failed(monkeypatch):
    """An error logged under a different site's logger name must not bleed
    into this site's result."""

    def fake_scrape_jobs(**kwargs):
        logging.getLogger("JobSpy:Glassdoor").error("Glassdoor: bad response status code: 403")
        return pd.DataFrame([{"title": "Bookkeeper", "company": "Acme", "location": "Remote"}])

    _install_fake_jobspy(monkeypatch, fake_scrape_jobs)

    client = JobSpyClient(max_retries_per_site=1)
    results = client.search(sites=["indeed"], search_term="bookkeeper")

    assert results[0].ok
    assert len(results[0].jobs) == 1


def test_one_board_failure_does_not_affect_other_boards(monkeypatch):
    def fake_scrape_jobs(**kwargs):
        if kwargs["site_name"] == ["zip_recruiter"]:
            logging.getLogger("JobSpy:ZipRecruiter").error("403 Response - Blocked")
            return pd.DataFrame()
        return pd.DataFrame([{"title": "Bookkeeper", "company": "Acme", "location": "Remote"}])

    _install_fake_jobspy(monkeypatch, fake_scrape_jobs)

    client = JobSpyClient(max_retries_per_site=1)
    results = client.search(sites=["zip_recruiter", "indeed"], search_term="bookkeeper")

    by_site = {r.site: r for r in results}
    assert not by_site["zip_recruiter"].ok
    assert by_site["indeed"].ok
    assert len(by_site["indeed"].jobs) == 1
