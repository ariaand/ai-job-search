from job_search.apply_bridge import TRACKER_COLUMNS, append_to_tracker_csv, build_apply_command, to_tracker_row
from job_search.models import Job


def make_job(**overrides) -> Job:
    defaults = dict(
        job_id="1",
        source="indeed",
        title="Remote Bookkeeper",
        company="Acme",
        location="Remote, USA",
        job_url="https://boards.example.com/job/1",
        direct_application_url=None,
        employment_type="fulltime",
        status="Ready to Apply",
        match_explanation="+20 remote; +15 title match",
    )
    defaults.update(overrides)
    return Job(**defaults)


def test_build_apply_command_uses_direct_url_when_present():
    job = make_job(direct_application_url="https://acme.com/careers/1")
    assert build_apply_command(job) == "/apply https://acme.com/careers/1"


def test_build_apply_command_falls_back_to_job_url():
    job = make_job()
    assert build_apply_command(job) == "/apply https://boards.example.com/job/1"


def test_to_tracker_row_has_all_expected_columns():
    row = to_tracker_row(make_job(), rating="Strong Match", date_str="2026-07-21")
    assert set(row.keys()) == set(TRACKER_COLUMNS)
    assert row["company"] == "Acme"
    assert row["role_type"] == "Full-time"
    assert row["fit_rating"] == "Strong Match"


def test_append_to_tracker_csv_creates_header_once(tmp_path):
    tracker_path = tmp_path / "tracker.csv"
    append_to_tracker_csv(make_job(job_id="1"), "Strong Match", "2026-07-21", tracker_path)
    append_to_tracker_csv(make_job(job_id="2", company="Beta"), "Good Match", "2026-07-22", tracker_path)

    lines = tracker_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(TRACKER_COLUMNS)
    assert len(lines) == 3  # header + 2 rows
    assert "Beta" in lines[2]
