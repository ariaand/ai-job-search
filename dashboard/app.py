"""Overview page. Run with: streamlit run dashboard/app.py

Other pages live in dashboard/pages/ (Streamlit's native multipage
convention - numbered filenames control sidebar order).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # allow `job_search`/`database` imports

import streamlit as st

from dashboard.data import get_db

st.set_page_config(page_title="Accounting Job Search", page_icon="\U0001F4CA", layout="wide")

st.title("Accounting Job Search - Overview")

db = get_db()
all_jobs = db.list_jobs()

today = __import__("datetime").date.today().isoformat()
jobs_today = [j for j in all_jobs if (j["date_discovered"] or "") == today]
high_match = [j for j in all_jobs if (j["match_score"] or 0) >= 80]
applied = [j for j in all_jobs if j["status"] not in ("New", "Reviewing", "Interested")]
interviews = [j for j in all_jobs if j["status"] == "Interview"]
offers = [j for j in all_jobs if j["status"] == "Offer"]
scored = [j["match_score"] for j in all_jobs if j["match_score"] is not None]
salaries = [j["salary_max"] or j["salary_min"] for j in all_jobs if j["salary_max"] or j["salary_min"]]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Jobs found today", len(jobs_today))
col2.metric("Total active jobs", len([j for j in all_jobs if j["status"] not in ("Rejected", "Archived")]))
col3.metric("High-match jobs (80+)", len(high_match))
col4.metric("Applications submitted", len(applied))

col5, col6, col7, col8 = st.columns(4)
col5.metric("Interviews", len(interviews))
col6.metric("Offers", len(offers))
col7.metric("Avg match score", f"{sum(scored) / len(scored):.0f}" if scored else "-")
col8.metric("Avg salary (when listed)", f"${sum(salaries) / len(salaries):,.0f}" if salaries else "-")

st.divider()
st.subheader("Recent search runs")
runs = db.recent_runs(limit=10)
if runs:
    st.dataframe(
        [dict(r) for r in runs],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No search runs yet. Go to the Job Search page to run one.")

st.caption(
    "This dashboard covers search, scoring, and tracking only. CV tailoring, cover letters, "
    "ATS analysis, and interview prep stay in Claude Code's `/apply` workflow - see the Job Detail "
    "page for the exact `/apply` command for any job."
)
