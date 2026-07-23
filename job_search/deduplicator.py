"""Deduplicates jobs across boards and across search runs.

Grouping key: normalized (company, title, location), OR an exact job_url
match. Within a group, description similarity (difflib) confirms the jobs
are really the same posting before merging - this guards against two
different roles at the same company normalizing to the same title bucket
(e.g. "Staff Accountant" openings in two different locations that both
normalize to the same city name).

When duplicates are found, keeps the "best" version by, in priority order:
1. Direct employer posting (job.direct_application_url set)
2. Most complete description (longest)
3. Salary included
4. Newest posting (date_posted)
5. Most reliable source (see SOURCE_PRIORITY)
"""

from __future__ import annotations

import re
from datetime import date, datetime
from difflib import SequenceMatcher

from job_search.models import Job

# Lower number = more reliable/preferred source when all else is tied.
SOURCE_PRIORITY: dict[str, int] = {
    "linkedin": 1,
    "indeed": 2,
    "glassdoor": 3,
    "zip_recruiter": 4,
    "google": 5,
}

DESCRIPTION_SIMILARITY_THRESHOLD = 0.6

_COMPANY_SUFFIXES = re.compile(r"\b(llc|inc|corp|corporation|co|ltd|company)\b\.?")
_NON_ALNUM = re.compile(r"[^a-z0-9 ]")


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = _NON_ALNUM.sub(" ", text)
    text = _COMPANY_SUFFIXES.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def group_key(job: Job) -> tuple[str, str, str]:
    return (normalize(job.company), normalize(job.title), normalize(job.location))


def _description_similarity(a: Job, b: Job) -> float:
    if not a.description or not b.description:
        return 0.0
    return SequenceMatcher(None, a.description, b.description).ratio()


def _is_same_posting(a: Job, b: Job) -> bool:
    if a.job_url and b.job_url and a.job_url == b.job_url:
        return True
    return _description_similarity(a, b) >= DESCRIPTION_SIMILARITY_THRESHOLD


def _recency_rank(date_posted: str | None) -> int:
    """Days-ago as an int, so smaller = newer. Missing/unparseable dates sort last."""
    if not date_posted:
        return 10**9
    try:
        parsed = datetime.fromisoformat(date_posted).date() if "T" in date_posted else date.fromisoformat(date_posted)
        return (date.today() - parsed).days
    except (ValueError, TypeError):
        return 10**9


def _rank(job: Job) -> tuple:
    """Sort key where the FIRST (best) item wins - lower tuple sorts first."""
    has_direct = 0 if job.direct_application_url else 1
    description_len = -(len(job.description or ""))
    has_salary = 0 if (job.salary_min or job.salary_max) else 1
    recency = _recency_rank(job.date_posted)
    source_priority = SOURCE_PRIORITY.get(job.source, 99)
    return (has_direct, description_len, has_salary, recency, source_priority)


def deduplicate(jobs: list[Job]) -> tuple[list[Job], int]:
    """Returns (deduplicated_jobs, number_of_duplicates_removed)."""
    buckets: dict[tuple[str, str, str], list[Job]] = {}
    for job in jobs:
        buckets.setdefault(group_key(job), []).append(job)

    kept: list[Job] = []
    duplicates_removed = 0

    for candidates in buckets.values():
        # Within a bucket, cluster further by actual same-posting check
        # (guards against normalization collisions across unrelated postings).
        clusters: list[list[Job]] = []
        for job in candidates:
            placed = False
            for cluster in clusters:
                if _is_same_posting(job, cluster[0]):
                    cluster.append(job)
                    placed = True
                    break
            if not placed:
                clusters.append([job])

        for cluster in clusters:
            if len(cluster) == 1:
                kept.append(cluster[0])
                continue
            duplicates_removed += len(cluster) - 1
            best = sorted(cluster, key=_rank)[0]
            kept.append(best)

    return kept, duplicates_removed
