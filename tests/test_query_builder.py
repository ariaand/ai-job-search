import pytest

from job_search.query_builder import CATEGORY_KEYWORD_HINTS, available_focuses, build_queries


TEST_TITLES = {
    "bookkeeping": ["Remote Bookkeeper", "Senior Bookkeeper"],
    "controller": ["Assistant Controller"],
}
TEST_HINTS = {"bookkeeping": "QuickBooks Online", "controller": ""}


def test_build_queries_single_focus():
    queries = build_queries("bookkeeping", job_titles=TEST_TITLES, category_keyword_hints=TEST_HINTS)
    assert len(queries) == 2
    assert all(q.focus == "bookkeeping" for q in queries)
    assert queries[0].search_term == "Remote Bookkeeper QuickBooks Online"


def test_build_queries_broad_covers_every_category():
    queries = build_queries("broad", job_titles=TEST_TITLES, category_keyword_hints=TEST_HINTS)
    assert len(queries) == 3
    focuses = {q.focus for q in queries}
    assert focuses == {"bookkeeping", "controller"}


def test_build_queries_unknown_focus_raises():
    with pytest.raises(ValueError, match="Unknown focus"):
        build_queries("not-a-real-focus", job_titles=TEST_TITLES)


def test_google_search_term_mentions_united_states():
    queries = build_queries("bookkeeping", job_titles=TEST_TITLES, category_keyword_hints=TEST_HINTS)
    assert all("United States" in q.google_search_term for q in queries)


def test_available_focuses_includes_broad():
    focuses = available_focuses(TEST_TITLES)
    assert "broad" in focuses
    assert "bookkeeping" in focuses


def test_no_hint_falls_back_to_bare_title():
    queries = build_queries("controller", job_titles=TEST_TITLES, category_keyword_hints=TEST_HINTS)
    assert queries[0].search_term == "Assistant Controller"


def test_category_keyword_hints_has_entry_for_every_real_category():
    # Guards against config/job_titles.yaml categories silently losing their hint.
    import yaml
    from pathlib import Path

    real_titles = yaml.safe_load(
        open(Path(__file__).resolve().parent.parent / "config" / "job_titles.yaml", encoding="utf-8")
    )
    for category in real_titles:
        assert category in CATEGORY_KEYWORD_HINTS
