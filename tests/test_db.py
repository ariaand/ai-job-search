import tempfile
from pathlib import Path

import pytest

from database.db import JobDatabase
from job_search.models import Job


@pytest.fixture()
def db(tmp_path: Path) -> JobDatabase:
    return JobDatabase(tmp_path / "test_jobs.db")


def make_job(**overrides) -> Job:
    defaults = dict(
        job_id="job-1",
        source="indeed",
        title="Staff Accountant",
        company="Acme",
        location="Remote, USA",
        match_score=85,
    )
    defaults.update(overrides)
    return Job(**defaults)


def test_upsert_new_job_returns_true(db: JobDatabase):
    assert db.upsert_job(make_job()) is True


def test_upsert_existing_job_returns_false(db: JobDatabase):
    db.upsert_job(make_job())
    assert db.upsert_job(make_job(match_score=90)) is False


def test_get_job_roundtrip(db: JobDatabase):
    db.upsert_job(make_job())
    row = db.get_job("job-1")
    assert row is not None
    assert row["title"] == "Staff Accountant"
    assert row["match_score"] == 85


def test_get_missing_job_returns_none(db: JobDatabase):
    assert db.get_job("does-not-exist") is None


def test_upsert_preserves_user_set_status(db: JobDatabase):
    db.upsert_job(make_job())
    db.update_status("job-1", "Applied", date_applied="2026-07-01")

    # A re-scrape of the same job (fresh score) must not clobber tracker state.
    db.upsert_job(make_job(match_score=70, notes="ignored"))
    row = db.get_job("job-1")
    assert row["status"] == "Applied"
    assert row["date_applied"] == "2026-07-01"
    assert row["match_score"] == 70  # scoring data does refresh


def test_list_jobs_filters_by_status(db: JobDatabase):
    db.upsert_job(make_job(job_id="a"))
    db.upsert_job(make_job(job_id="b"))
    db.update_status("a", "Applied")

    applied = db.list_jobs(status="Applied")
    assert len(applied) == 1
    assert applied[0]["job_id"] == "a"


def test_list_jobs_filters_by_min_score(db: JobDatabase):
    db.upsert_job(make_job(job_id="a", match_score=90))
    db.upsert_job(make_job(job_id="b", match_score=40))

    high = db.list_jobs(min_score=80)
    assert len(high) == 1
    assert high[0]["job_id"] == "a"


def test_search_run_lifecycle(db: JobDatabase):
    run_id = db.start_run("bookkeeping", ["indeed", "linkedin"])
    db.record_failed_source(run_id, "linkedin", "rate limited", attempts=2)
    db.finish_run(run_id, jobs_found=10, jobs_new=8, jobs_rejected=2, duplicates_removed=1)

    runs = db.recent_runs(limit=1)
    assert runs[0]["run_id"] == run_id
    assert runs[0]["jobs_found"] == 10
    assert runs[0]["finished_at"] is not None


def test_empty_database_list_jobs_returns_empty(db: JobDatabase):
    assert db.list_jobs() == []


def test_from_db_row_reconstructs_lists_and_bool(db: JobDatabase):
    job = make_job(
        job_id="j1",
        required_skills=["general ledger"],
        preferred_skills=["QuickBooks Online", "Xero"],
        red_flags=["CPA preferred"],
        cpa_required=True,
    )
    db.upsert_job(job)
    row = db.get_job("j1")

    rebuilt = Job.from_db_row(row)
    assert rebuilt.required_skills == ["general ledger"]
    assert rebuilt.preferred_skills == ["QuickBooks Online", "Xero"]
    assert rebuilt.red_flags == ["CPA preferred"]
    assert rebuilt.cpa_required is True
