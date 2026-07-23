"""Filterable results table. Selecting a job jumps to Job Detail."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from dashboard.data import STATUSES, get_db

st.set_page_config(page_title="Job Results", layout="wide")
st.title("Job Results")

db = get_db()

col1, col2, col3 = st.columns(3)
status_filter = col1.selectbox("Status", ["All"] + STATUSES)
min_score = col2.slider("Minimum match score", 0, 100, 0, step=5)
sort_by = col3.selectbox("Sort by", ["Match score (high to low)", "Date posted (newest)"])

rows = db.list_jobs(
    status=None if status_filter == "All" else status_filter,
    min_score=min_score or None,
    order_by="match_score DESC" if "score" in sort_by else "date_posted DESC",
)

if not rows:
    st.info("No jobs match these filters yet. Run a search on the Job Search page.")
else:
    st.write(f"{len(rows)} job(s)")
    for row in rows:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{row['title']}** @ {row['company']}")
                st.caption(f"{row['location']} · {row['source']} · {row['employment_type']} · posted {row['date_posted'] or 'unknown'}")
            with c2:
                st.metric("Score", row["match_score"])
                st.caption(row["status"])
            with c3:
                salary = None
                if row["salary_min"] or row["salary_max"]:
                    salary = f"${row['salary_min'] or 0:,.0f}-${row['salary_max'] or 0:,.0f}"
                st.write(salary or "Salary not listed")
                st.link_button("Open posting", row["job_url"], use_container_width=True)
            if row["red_flags"]:
                st.warning(f"Red flags: {row['red_flags']}")
            st.session_state.setdefault("selected_job_id", None)
            if st.button("View details ->", key=f"detail_{row['job_id']}"):
                st.session_state["selected_job_id"] = row["job_id"]
                st.switch_page("pages/3_Job_Detail.py")
