"""Full job detail: description, score breakdown, red flags, status control,
and the bridge into Claude Code's existing /apply workflow (no duplicate
resume/cover-letter/ATS generation here - that stays in /apply).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from dashboard.data import STATUSES, get_db
from job_search.apply_bridge import append_to_tracker_csv, build_apply_command
from job_search.models import Job
from job_search.scorer import get_score_breakdown

st.set_page_config(page_title="Job Detail", layout="wide")
st.title("Job Detail")

db = get_db()
rows = db.list_jobs()
if not rows:
    st.info("No jobs yet. Run a search on the Job Search page.")
    st.stop()

job_ids = [r["job_id"] for r in rows]
default_id = st.session_state.get("selected_job_id") or job_ids[0]
selected_id = st.selectbox(
    "Job",
    job_ids,
    index=job_ids.index(default_id) if default_id in job_ids else 0,
    format_func=lambda jid: next(f"{r['title']} @ {r['company']}" for r in rows if r["job_id"] == jid),
)
row = db.get_job(selected_id)

col_main, col_side = st.columns([2, 1])

with col_main:
    st.header(f"{row['title']} @ {row['company']}")
    st.caption(f"{row['location']} · {row['source']} · {row['employment_type']}")
    st.subheader("Description")
    st.write(row["description"] or "No description captured.")

with col_side:
    st.metric("Match score", row["match_score"])
    st.write("**Scoring explanation**")
    st.write(row["match_explanation"] or "-")

    if row["red_flags"]:
        st.write("**Red flags**")
        for flag in row["red_flags"].split(","):
            st.warning(flag.strip())

    if row["preferred_skills"]:
        st.write("**Matched software/skills**")
        st.write(row["preferred_skills"])

    salary = None
    if row["salary_min"] or row["salary_max"]:
        salary = f"${row['salary_min'] or 0:,.0f} - ${row['salary_max'] or 0:,.0f} ({row['salary_interval'] or 'n/a'})"
    st.write("**Salary**", salary or "Not listed")

    st.write("**Direct application URL**")
    st.write(row["direct_application_url"] or row["job_url"])

st.divider()
st.subheader("Tracking")

col_status, col_actions = st.columns([1, 2])
with col_status:
    new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(row["status"]) if row["status"] in STATUSES else 0)
    if st.button("Update status"):
        extra = {}
        if new_status == "Applied":
            extra["date_applied"] = date.today().isoformat()
        elif new_status == "Rejected":
            extra["rejection_date"] = date.today().isoformat()
        db.update_status(selected_id, new_status, **extra)
        st.success(f"Status updated to {new_status}")
        st.rerun()

with col_actions:
    job = Job.from_db_row(row)
    apply_command = build_apply_command(job)
    st.write("**Ready to apply?** Run this in Claude Code:")
    st.code(apply_command, language="bash")

    if st.button("Mark 'Ready to Apply' + add to tracker.csv", type="primary"):
        db.update_status(selected_id, "Ready to Apply")
        rating = get_score_breakdown(job).rating
        tracker_path = append_to_tracker_csv(job, rating=rating, date_str=date.today().isoformat())
        st.success(f"Added to {tracker_path.name} - now run `{apply_command}` in Claude Code.")
        st.rerun()

    col_a, col_b = st.columns(2)
    if col_a.button("Save"):
        db.update_status(selected_id, "Interested")
        st.rerun()
    if col_b.button("Archive"):
        db.update_status(selected_id, "Archived")
        st.rerun()
