from job_search.deduplicator import deduplicate, group_key, normalize
from job_search.models import Job


def make_job(**overrides) -> Job:
    defaults = dict(
        job_id="1",
        source="indeed",
        title="Staff Accountant",
        company="Acme Inc.",
        location="Remote, USA",
        description="A" * 500,
        job_url="https://example.com/job/1",
    )
    defaults.update(overrides)
    return Job(**defaults)


def test_normalize_strips_company_suffix_and_case():
    assert normalize("Acme Inc.") == "acme"
    assert normalize("Acme LLC") == "acme"
    assert normalize("ACME Corp") == "acme"


def test_group_key_matches_across_suffix_variants():
    a = make_job(company="Acme Inc.")
    b = make_job(company="Acme LLC")
    assert group_key(a) == group_key(b)


def test_dedup_removes_exact_url_duplicate():
    jobs = [make_job(job_id="1", source="indeed"), make_job(job_id="2", source="linkedin")]
    deduped, removed = deduplicate(jobs)
    assert len(deduped) == 1
    assert removed == 1


def test_dedup_prefers_direct_application_url():
    a = make_job(job_id="1", job_url="https://boardA.com/1", direct_application_url=None)
    b = make_job(job_id="2", job_url="https://boardA.com/1", direct_application_url="https://acme.com/careers/1")
    deduped, _ = deduplicate([a, b])
    assert deduped[0].job_id == "2"


def test_dedup_prefers_longer_description_when_no_direct_url():
    a = make_job(job_id="1", job_url="https://boardA.com/1", description="short")
    b = make_job(job_id="2", job_url="https://boardA.com/1", description="a much longer description " * 10)
    deduped, _ = deduplicate([a, b])
    assert deduped[0].job_id == "2"


def test_dedup_keeps_unrelated_jobs_separate():
    a = make_job(job_id="1", company="Acme", title="Staff Accountant", location="Remote")
    b = make_job(job_id="2", company="Beta", title="Bookkeeper", location="Remote", job_url="https://x.com/2")
    deduped, removed = deduplicate([a, b])
    assert len(deduped) == 2
    assert removed == 0


def test_dedup_empty_list():
    deduped, removed = deduplicate([])
    assert deduped == []
    assert removed == 0


def test_dedup_no_duplicates_returns_all():
    jobs = [
        make_job(job_id=str(i), company=f"Company{i}", job_url=f"https://x.com/{i}", description=f"Unique role {i} " * 20)
        for i in range(3)
    ]
    deduped, removed = deduplicate(jobs)
    assert len(deduped) == 3
    assert removed == 0
