"""Shared data-access helpers for the Streamlit dashboard pages."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from database.db import JobDatabase
from job_search.scorer import load_settings

REPO_ROOT = Path(__file__).resolve().parent.parent


@st.cache_resource
def get_db() -> JobDatabase:
    settings = load_settings()
    return JobDatabase(settings.get("database", {}).get("path"))


STATUSES = [
    "New",
    "Reviewing",
    "Interested",
    "Resume Generated",
    "Cover Letter Generated",
    "Ready to Apply",
    "Applied",
    "Follow-Up Due",
    "Interview",
    "Offer",
    "Rejected",
    "Archived",
]
