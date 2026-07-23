"""Hard-reject filters, applied before scoring/dedup/storage.

Anything that fails `passes_filters` never reaches the database - it is not
scored, not stored, not shown. Soft penalties (hybrid, missing salary, stale,
seasonal-tax) are NOT applied here; those are scored in job_search/scorer.py
so the job stays visible with an explanation instead of silently vanishing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from job_search.models import Job

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class FilterResult:
    passed: bool
    reason: Optional[str] = None


def load_exclusions(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(open(path or CONFIG_DIR / "exclusions.yaml", "r", encoding="utf-8")) or {}


def load_filter_settings(path: Optional[Path] = None) -> dict:
    settings = yaml.safe_load(open(path or CONFIG_DIR / "settings.yaml", "r", encoding="utf-8")) or {}
    return settings.get("filters", {})


def _text_blob(job: Job) -> str:
    return f"{job.title}\n{job.description}".lower()


def passes_filters(
    job: Job,
    exclusions: Optional[dict] = None,
    filter_settings: Optional[dict] = None,
) -> FilterResult:
    """Returns FilterResult(passed=False, reason=...) for the first exclusion
    hit, or FilterResult(passed=True) if the job clears every hard rule."""

    exclusions = exclusions if exclusions is not None else load_exclusions()
    filter_settings = filter_settings if filter_settings is not None else load_filter_settings()
    blob = _text_blob(job)

    # Remote / hybrid / onsite policy
    allow_hybrid = filter_settings.get("allow_hybrid", False)
    allow_onsite = filter_settings.get("allow_onsite", False)
    remote_only = filter_settings.get("remote_only", True)

    if remote_only and job.remote_status == "onsite" and not allow_onsite:
        return FilterResult(False, "Onsite-only job")
    if job.remote_status == "hybrid" and not allow_hybrid:
        return FilterResult(False, "Hybrid-only job (enable hybrid to allow)")

    # US-only / no relocation
    if exclusions.get("non_us") and job.location:
        loc_lower = job.location.lower()
        non_us_markers = ["canada", "united kingdom", "india", "philippines", " uk", "mexico"]
        if any(marker in loc_lower for marker in non_us_markers):
            return FilterResult(False, "Location outside the United States")

    if exclusions.get("relocation_required") and (
        "relocation required" in blob or "must relocate" in blob
    ):
        return FilterResult(False, "Requires relocation")

    # Keyword-based hard rejects
    for rule in exclusions.get("reject", []):
        for keyword in rule.get("keywords", []):
            if keyword.lower() in blob:
                return FilterResult(False, rule.get("reason", f"Matched reject keyword: {keyword}"))

    # Salary floor, if configured
    min_salary = filter_settings.get("min_salary_usd")
    if min_salary is not None and job.salary_max is not None and job.salary_max < min_salary:
        return FilterResult(False, f"Salary below floor of ${min_salary}")

    return FilterResult(True)


def filter_jobs(
    jobs: list[Job],
    exclusions: Optional[dict] = None,
    filter_settings: Optional[dict] = None,
) -> tuple[list[Job], list[tuple[Job, str]]]:
    """Split jobs into (passed, rejected) where rejected carries the reason."""
    exclusions = exclusions if exclusions is not None else load_exclusions()
    filter_settings = filter_settings if filter_settings is not None else load_filter_settings()

    passed: list[Job] = []
    rejected: list[tuple[Job, str]] = []
    for job in jobs:
        result = passes_filters(job, exclusions, filter_settings)
        if result.passed:
            passed.append(job)
        else:
            rejected.append((job, result.reason or "excluded"))
    return passed, rejected
