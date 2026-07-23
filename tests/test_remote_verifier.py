from job_search.remote_verifier import verify_remote_status


def test_detects_onsite_from_work_location_field():
    desc = "Great team!\n\nWork Location: In person"
    result = verify_remote_status(desc, current_status="remote")
    assert result.remote_status == "onsite"
    assert result.changed is True
    assert result.source == "indeed_work_location_field"


def test_detects_remote_from_work_location_field():
    desc = "Join us.\nWork Location: Remote"
    result = verify_remote_status(desc, current_status="unknown")
    assert result.remote_status == "remote"
    assert result.changed is True


def test_detects_hybrid_from_work_location_field():
    desc = "Nice role.\nWork Location: Hybrid remote in Denver, CO 80202"
    result = verify_remote_status(desc, current_status="remote")
    assert result.remote_status == "hybrid"
    assert result.changed is True


def test_no_work_location_field_leaves_status_unchanged():
    desc = "A job description with no structured location field at all."
    result = verify_remote_status(desc, current_status="remote")
    assert result.remote_status == "remote"
    assert result.changed is False
    assert result.source == "unchanged"


def test_matching_status_reports_unchanged():
    desc = "Work Location: Remote"
    result = verify_remote_status(desc, current_status="remote")
    assert result.changed is False


def test_case_insensitive_field_match():
    desc = "WORK LOCATION: IN PERSON"
    result = verify_remote_status(desc, current_status="remote")
    assert result.remote_status == "onsite"


def test_empty_description_leaves_status_unchanged():
    result = verify_remote_status("", current_status="remote")
    assert result.remote_status == "remote"
    assert result.changed is False


def test_none_description_does_not_raise():
    result = verify_remote_status(None, current_status="remote")
    assert result.remote_status == "remote"
    assert result.changed is False
