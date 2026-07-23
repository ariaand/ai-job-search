"""Batch review queue: pick several scored jobs, promote them to
"Ready to Apply" together, and get every /apply command in one place so you
can run them back-to-back in Claude Code in one sitting.

No job is ever submitted automatically here - this only prepares the batch
and lets you mark each one "Applied" once you've actually run /apply and
sent it yourself.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from dashboard.data import get_db
from job_search.apply_bridge import append_to_tracker_csv, build_apply_command
from job_search.models import Job
from job_search.scorer import get_score_breakdown

st.set_page_config(page_title="Review Queue", layout="wide")
st.title("Batch Review Queue")
st.caption(
    "Select several jobs, promote them to 'Ready to Apply' in one batch, then run each "
    "/apply command yourself in Claude Code. Nothing here submits an application - "
    "you still review and send every one."
)

db = get_db()

st.subheader("1. Build the queue")
candidates = db.list_jobs(status=None, min_score=st.slider("Minimum score to consider", 0, 100, 70, step=5))
candidates = [row for row in candidates if row["status"] in ("New", "Reviewing", "Interested")]

if not candidates:
    st.info("No jobs at or above that score with status New/Reviewing/Interested. Lower the threshold or run a search.")
else:
    options = {row["job_id"]: f"[{row['match_score']}] {row['title']} @ {row['company']}" for row in candidates}
    selected_ids = st.multiselect(
        "Add to queue",
        options=list(options.keys()),
        format_func=lambda jid: options[jid],
        default=list(options.keys())[:10],
    )

    if st.button(f"Promote {len(selected_ids)} job(s) to 'Ready to Apply'", type="primary", disabled=not selected_ids):
        for job_id in selected_ids:
            db.update_status(job_id, "Ready to Apply")
        st.success(f"Promoted {len(selected_ids)} job(s). See the queue below.")
        st.rerun()

st.divider()
st.subheader("2. Your queue - run these in Claude Code, one at a time")

queue = db.list_jobs(status="Ready to Apply")
if not queue:
    st.info("Queue is empty. Promote some jobs above.")
else:
    all_commands = []
    for row in queue:
        job = Job.from_db_row(row)
        command = build_apply_command(job)
        all_commands.append(command)

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{job.title}** @ {job.company} — score {job.match_score}")
                st.caption(row["location"])
                st.code(command, language="bash")
            with col2:
                if st.button("Mark Applied", key=f"applied_{job.job_id}"):
                    db.update_status(job.job_id, "Applied", date_applied=date.today().isoformat())
                    # Re-fetch after the update - `job` above is a pre-update
                    # snapshot, so writing it straight to the tracker would
                    # record the stale "Ready to Apply" status instead of
                    # "Applied".
                    applied_job = Job.from_db_row(db.get_job(job.job_id))
                    rating = get_score_breakdown(applied_job).rating
                    append_to_tracker_csv(applied_job, rating=rating, date_str=date.today().isoformat())
                    st.rerun()
                if st.button("Remove from queue", key=f"remove_{job.job_id}"):
                    db.update_status(job.job_id, "Reviewing")
                    st.rerun()

    st.write("**Copy all commands (paste into Claude Code one at a time):**")
    st.code("\n".join(all_commands), language="bash")
