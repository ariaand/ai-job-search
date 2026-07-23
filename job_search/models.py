"""Data model for a scraped/scored job posting.

`Job` mirrors the SQLite schema in database/schema.py field-for-field so
records can be passed straight from JobSpy -> filters -> dedup -> scorer -> db
without remapping. Use `Job.from_jobspy_row` to build one from a raw JobSpy
DataFrame row.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Any, Optional

from job_search.remote_verifier import verify_remote_status


@dataclass
class Job:
    # Identity / source
    job_id: str
    source: str
    title: str
    company: str
    location: str

    # Classification
    remote_status: str = "unknown"       # "remote" | "hybrid" | "onsite" | "unknown"
    employment_type: str = "unknown"     # "fulltime" | "parttime" | "contract" | "temporary" | "unknown"

    # Compensation
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_interval: Optional[str] = None  # "yearly" | "hourly" | etc.

    # Dates
    date_posted: Optional[str] = None      # ISO date string, from source
    date_discovered: str = field(default_factory=lambda: date.today().isoformat())

    # Links & content
    job_url: str = ""
    direct_application_url: Optional[str] = None
    description: str = ""

    # Skills extracted at scoring time
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    cpa_required: bool = False
    years_experience_required: Optional[int] = None

    # Scoring (populated by job_search/scorer.py)
    match_score: Optional[int] = None
    match_explanation: str = ""
    red_flags: list[str] = field(default_factory=list)

    # Tracking (mutable after discovery)
    status: str = "New"
    notes: str = ""
    date_applied: Optional[str] = None
    follow_up_date: Optional[str] = None
    interview_date: Optional[str] = None
    rejection_date: Optional[str] = None
    offer_status: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["required_skills"] = ",".join(self.required_skills)
        d["preferred_skills"] = ",".join(self.preferred_skills)
        d["red_flags"] = ",".join(self.red_flags)
        return d

    @staticmethod
    def from_db_row(row: Any) -> "Job":
        """Reconstructs a Job from a sqlite3.Row (database/db.py), splitting
        the comma-joined list columns back into lists and coercing SQLite's
        0/1 integer back to bool for cpa_required."""
        data = dict(row)
        data["required_skills"] = [s for s in (data.get("required_skills") or "").split(",") if s]
        data["preferred_skills"] = [s for s in (data.get("preferred_skills") or "").split(",") if s]
        data["red_flags"] = [s for s in (data.get("red_flags") or "").split(",") if s]
        data["cpa_required"] = bool(data.get("cpa_required"))
        return Job(**data)

    @staticmethod
    def from_jobspy_row(row: dict[str, Any], source: str) -> "Job":
        """Build a Job from one row of JobSpy's `scrape_jobs()` DataFrame (as a dict)."""

        def _clean(value: Any) -> Any:
            # pandas gives NaN for missing values; normalize to None.
            if value is None:
                return None
            if isinstance(value, float) and value != value:  # NaN check without numpy/pandas import
                return None
            return value

        title = str(_clean(row.get("title")) or "").strip()
        company = str(_clean(row.get("company")) or "").strip()
        location = str(_clean(row.get("location")) or "").strip()
        job_url = str(_clean(row.get("job_url")) or "")

        description = str(_clean(row.get("description")) or "")

        is_remote = _clean(row.get("is_remote"))
        remote_status = "remote" if is_remote else "unknown"
        # JobSpy's is_remote flag is unreliable (seen misclassifying onsite/hybrid
        # postings as remote in practice) - Indeed's own "Work Location:" field in
        # the description is ground truth when present. See remote_verifier.py.
        remote_status = verify_remote_status(description, remote_status).remote_status

        job_type_raw = str(_clean(row.get("job_type")) or "").lower()
        employment_type = "unknown"
        for et in ("fulltime", "parttime", "contract", "temporary", "internship"):
            if et in job_type_raw:
                employment_type = et
                break

        date_posted = _clean(row.get("date_posted"))
        if isinstance(date_posted, (date, datetime)):
            date_posted = date_posted.isoformat()
        elif date_posted is not None:
            date_posted = str(date_posted)

        job_id = str(_clean(row.get("id")) or job_url or f"{source}:{company}:{title}:{location}")

        return Job(
            job_id=job_id,
            source=source,
            title=title,
            company=company,
            location=location,
            remote_status=remote_status,
            employment_type=employment_type,
            salary_min=_clean(row.get("min_amount")),
            salary_max=_clean(row.get("max_amount")),
            salary_interval=_clean(row.get("interval")),
            date_posted=date_posted,
            job_url=job_url,
            direct_application_url=_clean(row.get("job_url_direct")) or None,
            description=description,
        )
