"""Run controls: focus category, boards, result count, date range, remote-only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from job_search.query_builder import available_focuses
from job_search.scorer import load_settings
from job_search.search_service import run_search

st.set_page_config(page_title="Job Search", layout="wide")
st.title("Run a Job Search")

settings = load_settings()
all_sites = settings["search"].get("sites", [])
focuses = [f for f in available_focuses() if f != "broad"] + ["broad"]

with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        focus = st.selectbox("Focus category", focuses, index=focuses.index("broad"))
        sites = st.multiselect("Job boards", all_sites, default=all_sites)
        results_wanted = st.slider("Results per query", 10, 100, settings["search"].get("results_wanted_per_query", 50), step=10)
    with col2:
        days_back = st.slider("Posted within (days)", 1, 30, 14)
        remote_only = st.checkbox("Remote only", value=settings["filters"].get("remote_only", True))
        employment_types = st.multiselect(
            "Employment type",
            ["fulltime", "parttime", "contract", "temporary", "internship"],
            default=["fulltime", "parttime", "contract", "temporary"],
        )
    dry_run = st.checkbox("Dry run (search + score, don't save)", value=False)
    submitted = st.form_submit_button("Run Search", type="primary")

if submitted:
    if not sites:
        st.error("Select at least one job board.")
    else:
        with st.spinner(f"Searching {', '.join(sites)} for '{focus}'..."):
            result = run_search(
                focus,
                dry_run=dry_run,
                search_overrides={
                    "sites": sites,
                    "results_wanted_per_query": results_wanted,
                    "hours_old": days_back * 24,
                    "is_remote": remote_only,
                },
            )

        st.success(
            f"Found {result.jobs_found} · rejected {result.jobs_rejected} · "
            f"deduped {result.duplicates_removed} · new {result.jobs_new} · updated {result.jobs_updated}"
        )

        if result.failed_sites:
            with st.expander(f"{len(result.failed_sites)} board(s) failed (others still ran)"):
                for f in result.failed_sites:
                    st.write(f"**{f.site}**: {f.error}")

        if result.top_jobs:
            st.subheader("Top matches this run")
            st.dataframe(
                [
                    {
                        "Score": j.match_score,
                        "Title": j.title,
                        "Company": j.company,
                        "Location": j.location,
                        "Salary": f"${j.salary_min:,.0f}-${j.salary_max:,.0f}" if j.salary_min or j.salary_max else "-",
                        "URL": j.job_url,
                    }
                    for j in result.top_jobs
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.page_link("pages/2_Job_Results.py", label="View all results ->")
