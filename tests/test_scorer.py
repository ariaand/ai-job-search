from datetime import date, timedelta

from job_search.models import Job
from job_search.scorer import score_job


SETTINGS = {
    "search": {"recent_priority_days": 7},
    "filters": {"max_posting_age_days": 14},
    "scoring": {
        "weights": {
            "remote": 20,
            "flexible_schedule": 10,
            "title_match": 15,
            "software_match": 10,
            "accounting_experience_match": 15,
            "excel_reconciliation_match": 10,
            "preferred_employment_type": 5,
            "salary_listed": 5,
            "recency_bonus_days": 5,
            "direct_employer_application": 5,
        },
        "deductions": {
            "cpa_mandatory": 30,
            "hybrid_only": 25,
            "missing_salary": 3,
            "stale_posting": 10,
            "experience_gap": 15,
        },
        "rating_bands": [
            {"min": 90, "max": 100, "label": "Apply Immediately"},
            {"min": 80, "max": 89, "label": "Strong Match"},
            {"min": 70, "max": 79, "label": "Good Match"},
            {"min": 60, "max": 69, "label": "Review Carefully"},
            {"min": 0, "max": 59, "label": "Low Priority"},
        ],
    },
}
SKILLS_CONFIG = {
    "software": ["QuickBooks Online", "Xero"],
    "accounting_process": ["bank reconciliation", "general ledger", "month-end close"],
    "administrative": [],
}
EXCLUSIONS = {"penalty": [], "flag": []}
CANDIDATE_PROFILE = {"skills": ["Bank reconciliations"], "preferred_work": {"employment_types_preferred": ["fulltime_w2"]}}


def make_job(**overrides) -> Job:
    defaults = dict(
        job_id="1",
        source="indeed",
        title="Remote Bookkeeper",
        company="Acme",
        location="Remote, USA",
        remote_status="remote",
        employment_type="fulltime",
        description="QuickBooks Online bank reconciliation and general ledger work.",
        salary_min=50000,
        salary_max=60000,
        date_posted=date.today().isoformat(),
        direct_application_url="https://acme.com/careers/1",
    )
    defaults.update(overrides)
    return Job(**defaults)


def _score(job, target_titles=None):
    return score_job(
        job,
        settings=SETTINGS,
        skills_config=SKILLS_CONFIG,
        exclusions=EXCLUSIONS,
        candidate_profile=CANDIDATE_PROFILE,
        target_titles=target_titles,
    )


def test_high_match_job_scores_high():
    job = _score(make_job(), target_titles=["Remote Bookkeeper"])
    assert job.match_score >= 80
    assert job.match_score <= 100


def test_score_is_clamped_0_to_100():
    job = _score(make_job(description="CPA required. Insurance sales. Hybrid only.", remote_status="hybrid"))
    assert 0 <= job.match_score <= 100


def test_cpa_mandatory_applies_large_deduction_and_flag():
    baseline = _score(make_job(job_id="a")).match_score
    with_cpa = _score(make_job(job_id="b", description="CPA required for this role. QuickBooks Online bank reconciliation general ledger."))
    assert with_cpa.match_score < baseline
    assert with_cpa.cpa_required is True
    assert any("CPA" in flag for flag in with_cpa.red_flags)


def test_cpa_preferred_flags_but_does_not_deduct():
    job = _score(make_job(description="CPA preferred but not required. QuickBooks Online bank reconciliation general ledger."))
    assert job.cpa_required is False
    assert any("CPA preferred" in flag for flag in job.red_flags)


def test_hybrid_deducts_points():
    remote_score = _score(make_job(job_id="a")).match_score
    hybrid_score = _score(make_job(job_id="b", remote_status="hybrid")).match_score
    assert hybrid_score < remote_score


def test_missing_salary_small_deduction():
    with_salary = _score(make_job(job_id="a")).match_score
    without_salary = _score(make_job(job_id="b", salary_min=None, salary_max=None)).match_score
    assert without_salary == with_salary - 3 - 5  # loses salary_listed bonus too


def test_stale_posting_deducted_and_flagged():
    old_date = (date.today() - timedelta(days=30)).isoformat()
    job = _score(make_job(date_posted=old_date))
    assert any("days old" in flag for flag in job.red_flags)


def test_recent_posting_gets_recency_bonus():
    recent = _score(make_job(job_id="a", date_posted=date.today().isoformat())).match_score
    stale = _score(make_job(job_id="b", date_posted=(date.today() - timedelta(days=30)).isoformat())).match_score
    assert recent > stale


def test_software_match_populates_matching_skills():
    job = _score(make_job())
    assert "QuickBooks Online" in job.preferred_skills


def test_no_software_match_leaves_preferred_skills_empty():
    job = _score(make_job(description="General office admin duties."))
    assert job.preferred_skills == []


def test_rating_label_present_in_explanation_via_breakdown():
    from job_search.scorer import get_score_breakdown

    job = _score(make_job(), target_titles=["Remote Bookkeeper"])
    breakdown = get_score_breakdown(job)
    assert breakdown.rating in {"Apply Immediately", "Strong Match", "Good Match", "Review Carefully", "Low Priority"}
    assert breakdown.recommendation
