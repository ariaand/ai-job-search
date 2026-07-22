"""Application tracker - one column per status."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from dashboard.data import STATUSES, get_db

st.set_page_config(page_title="Application Tracker", layout="wide")
st.title("Application Tracker")

db = get_db()
all_jobs = db.list_jobs()
by_status = {status: [j for j in all_jobs if j["status"] == status] for status in STATUSES}

active_statuses = [s for s in STATUSES if s not in ("Rejected", "Archived")]
cols = st.columns(len(active_statuses))

for col, status in zip(cols, active_statuses):
    with col:
        st.markdown(f"**{status}** ({len(by_status[status])})")
        for job in by_status[status]:
            with st.container(border=True):
                st.caption(f"{job['title']}")
                st.caption(job["company"])
                st.caption(f"Score: {job['match_score']}")

with st.expander(f"Rejected ({len(by_status['Rejected'])}) / Archived ({len(by_status['Archived'])})"):
    for job in by_status["Rejected"] + by_status["Archived"]:
        st.write(f"{job['title']} @ {job['company']} - {job['status']}")
