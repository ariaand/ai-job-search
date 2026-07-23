"""Bridges a scored job into the existing Claude-Code application workflow.

This engine deliberately does NOT generate a second CV/cover letter. Once a
job is marked "Ready to Apply", this module hands it to the existing
`/apply` skill (LaTeX CV + cover letter, drafter-reviewer, PDF verification)
and appends a row to `job_search_tracker.csv` in its established column
format, so both workflows share one tracker.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from job_search.models import Job

TRACKER_COLUMNS = [
    "date",
    "company",
    "sector",
    "role",
    "role_type",
    "channel",
    "status",
    "contact_person",
    "fit_rating",
    "notes",
    "cv_file",
    "cover_letter_file",
    "source",
]

_ROLE_TYPE_LABELS = {
    "fulltime": "Full-time",
    "parttime": "Part-time",
    "contract": "Contract",
    "temporary": "Temporary",
    "internship": "Internship",
    "unknown": "",
}


def build_apply_command(job: Job) -> str:
    """The exact `/apply` invocation to run in Claude Code for this job."""
    target = job.direct_application_url or job.job_url
    return f"/apply {target}"


def to_tracker_row(job: Job, rating: str, date_str: str) -> dict[str, str]:
    return {
        "date": date_str,
        "company": job.company,
        "sector": "Accounting/Bookkeeping",
        "role": job.title,
        "role_type": _ROLE_TYPE_LABELS.get(job.employment_type, job.employment_type),
        "channel": job.source,
        "status": job.status,
        "contact_person": "",
        "fit_rating": rating,
        "notes": job.match_explanation,
        "cv_file": "",
        "cover_letter_file": "",
        "source": job.job_url,
    }


def append_to_tracker_csv(
    job: Job,
    rating: str,
    date_str: str,
    tracker_path: Optional[Path] = None,
) -> Path:
    """Appends one row to job_search_tracker.csv, creating it with the
    existing header if it doesn't exist yet. Never overwrites existing rows."""
    path = Path(tracker_path) if tracker_path else Path(__file__).resolve().parent.parent / "job_search_tracker.csv"
    row = to_tracker_row(job, rating, date_str)

    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=TRACKER_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return path
