import pytest

from job_search.filters import filter_jobs, passes_filters
from job_search.models import Job


EXCLUSIONS = {
    "reject": [
        {"keywords": ["commission only"], "reason": "Commission-only compensation"},
        {"keywords": ["insurance sales"], "reason": "Insurance sales role"},
        {"keywords": ["mlm"], "reason": "MLM opportunity"},
        {"keywords": ["cpa required"], "reason": "CPA license mandatory"},
    ],
    "penalty": [],
    "flag": [],
    "relocation_required": True,
    "non_us": True,
}
FILTER_SETTINGS = {"remote_only": True, "allow_hybrid": False, "allow_onsite": False, "min_salary_usd": None}


def make_job(**overrides) -> Job:
    defaults = dict(
        job_id="1",
        source="indeed",
        title="Remote Bookkeeper",
        company="Acme LLC",
        location="United States",
        remote_status="remote",
        description="QuickBooks Online bookkeeping role.",
    )
    defaults.update(overrides)
    return Job(**defaults)


def test_passes_clean_remote_job():
    result = passes_filters(make_job(), EXCLUSIONS, FILTER_SETTINGS)
    assert result.passed


def test_rejects_onsite_only():
    job = make_job(remote_status="onsite")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed
    assert "Onsite" in result.reason


def test_rejects_hybrid_when_disabled():
    job = make_job(remote_status="hybrid")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed


def test_allows_hybrid_when_enabled():
    settings = {**FILTER_SETTINGS, "allow_hybrid": True}
    job = make_job(remote_status="hybrid")
    result = passes_filters(job, EXCLUSIONS, settings)
    assert result.passed


def test_rejects_commission_only():
    job = make_job(description="This is a commission only sales position.")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed
    assert "Commission" in result.reason


def test_rejects_insurance_sales():
    job = make_job(title="Insurance Sales Agent", description="Sell insurance policies.")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed


def test_rejects_mlm():
    job = make_job(description="Join our MLM opportunity today!")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed


def test_rejects_cpa_mandatory():
    job = make_job(description="CPA required for this role.")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed


def test_rejects_non_us_location():
    job = make_job(location="Toronto, Canada")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed


def test_rejects_relocation_required():
    job = make_job(description="Relocation required for this position.")
    result = passes_filters(job, EXCLUSIONS, FILTER_SETTINGS)
    assert not result.passed


def test_enforces_salary_floor_when_configured():
    settings = {**FILTER_SETTINGS, "min_salary_usd": 60000}
    job = make_job(salary_min=40000, salary_max=50000)
    result = passes_filters(job, EXCLUSIONS, settings)
    assert not result.passed


def test_filter_jobs_splits_passed_and_rejected():
    jobs = [make_job(job_id="1"), make_job(job_id="2", remote_status="onsite")]
    passed, rejected = filter_jobs(jobs, EXCLUSIONS, FILTER_SETTINGS)
    assert len(passed) == 1
    assert len(rejected) == 1
    assert rejected[0][0].job_id == "2"


def test_empty_job_list_returns_empty():
    passed, rejected = filter_jobs([], EXCLUSIONS, FILTER_SETTINGS)
    assert passed == []
    assert rejected == []
