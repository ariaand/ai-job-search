import pytest

from database.db import JobDatabase
from job_search.models import Job
from job_search.scorer import score_job
from job_search.search_service import reverify_remote_status


@pytest.fixture()
def db(tmp_path) -> JobDatabase:
    return JobDatabase(tmp_path / "test_jobs.db")


def make_job(**overrides) -> Job:
    defaults = dict(
        job_id="job-1",
        source="indeed",
        title="Bookkeeper",
        company="Acme",
        location="Remote, USA",
        remote_status="remote",
        description="A great bookkeeping role.\n\nWork Location: In person",
        status="New",
    )
    defaults.update(overrides)
    job = Job(**defaults)
    score_job(job)
    return job


def test_reverify_corrects_misclassified_onsite_job(db: JobDatabase):
    db.upsert_job(make_job())
    result = reverify_remote_status(db=db)

    assert result.total_checked == 1
    assert result.corrected == 1
    row = db.get_job("job-1")
    assert row["remote_status"] == "onsite"


def test_reverify_rejects_new_status_job_that_becomes_onsite(db: JobDatabase):
    db.upsert_job(make_job(status="New"))
    result = reverify_remote_status(db=db)

    assert result.newly_rejected == 1
    row = db.get_job("job-1")
    assert row["status"] == "Rejected"


def test_reverify_does_not_touch_already_applied_job(db: JobDatabase):
    db.upsert_job(make_job(status="Applied"))
    result = reverify_remote_status(db=db)

    assert result.corrected == 1  # remote_status/score still corrected
    assert result.newly_rejected == 0  # but status is preserved
    row = db.get_job("job-1")
    assert row["status"] == "Applied"
    assert row["remote_status"] == "onsite"  # score/classification still fixed


def test_reverify_leaves_genuinely_remote_job_alone(db: JobDatabase):
    db.upsert_job(make_job(description="Work Location: Remote", remote_status="remote"))
    result = reverify_remote_status(db=db)

    assert result.corrected == 0
    row = db.get_job("job-1")
    assert row["remote_status"] == "remote"
    assert row["status"] == "New"


def test_reverify_leaves_job_alone_when_no_work_location_field(db: JobDatabase):
    db.upsert_job(make_job(description="No structured field here at all.", remote_status="remote"))
    result = reverify_remote_status(db=db)

    assert result.corrected == 0


def test_reverify_empty_database(db: JobDatabase):
    result = reverify_remote_status(db=db)
    assert result.total_checked == 0
    assert result.corrected == 0
