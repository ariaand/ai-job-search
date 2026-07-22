"""Orchestrates a full search run: query_builder -> jobspy_client -> filters
-> deduplicator -> scorer -> database. This is the single entry point both
app.py (CLI) and dashboard/pages use to run a search.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from database.db import JobDatabase
from job_search.deduplicator import deduplicate
from job_search.filters import filter_jobs, load_exclusions, load_filter_settings
from job_search.jobspy_client import BoardResult, JobSpyClient
from job_search.models import Job
from job_search.query_builder import build_queries, load_job_titles
from job_search.scorer import load_candidate_profile, load_settings, load_skills_config, score_job

logger = logging.getLogger(__name__)


@dataclass
class SearchRunResult:
    focus: str
    run_id: int
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    jobs_rejected: int = 0
    duplicates_removed: int = 0
    failed_sites: list[BoardResult] = field(default_factory=list)
    top_jobs: list[Job] = field(default_factory=list)


def run_search(
    focus: str,
    settings_path: Optional[Path] = None,
    db: Optional[JobDatabase] = None,
    dry_run: bool = False,
    search_overrides: Optional[dict] = None,
) -> SearchRunResult:
    """Runs one search for `focus` (or "broad" for every category), scores
    and stores results. Board failures are collected, not raised - a bad
    board never aborts the run.

    `search_overrides` merges onto config/settings.yaml's `search` section
    for this run only (e.g. {"sites": [...], "hours_old": 168}) - used by
    the dashboard's search controls without mutating the config file."""

    settings = load_settings(settings_path)
    search_cfg = {**settings["search"], **(search_overrides or {})}
    job_titles = load_job_titles()
    skills_config = load_skills_config()
    exclusions = load_exclusions()
    filter_settings = load_filter_settings()
    candidate_profile = load_candidate_profile()

    database = db or JobDatabase(settings.get("database", {}).get("path"))
    queries = build_queries(focus, job_titles=job_titles)
    target_titles = job_titles.get(focus, [t for titles in job_titles.values() for t in titles])

    client = JobSpyClient(
        results_wanted=search_cfg.get("results_wanted_per_query", 50),
        hours_old=search_cfg.get("hours_old", 336),
        country_indeed=search_cfg.get("country_indeed", "USA"),
        max_retries_per_site=search_cfg.get("max_retries_per_site", 2),
        site_timeout_seconds=search_cfg.get("site_timeout_seconds", 60),
    )

    run_id = -1 if dry_run else database.start_run(focus, search_cfg.get("sites", []))

    all_jobs: list[Job] = []
    failed_sites: list[BoardResult] = []

    for query in queries:
        board_results = client.search(
            sites=search_cfg.get("sites", []),
            search_term=query.search_term,
            location=search_cfg.get("location", "United States"),
            is_remote=search_cfg.get("is_remote", True),
            google_search_term=query.google_search_term,
        )
        for board_result in board_results:
            if not board_result.ok:
                logger.warning("Search failed: site=%s error=%s", board_result.site, board_result.error)
                failed_sites.append(board_result)
                if not dry_run:
                    database.record_failed_source(
                        run_id, board_result.site, board_result.error or "unknown", board_result.attempts
                    )
                continue
            for row in board_result.jobs:
                all_jobs.append(Job.from_jobspy_row(row, source=board_result.site))

    passed, rejected = filter_jobs(all_jobs, exclusions=exclusions, filter_settings=filter_settings)
    deduped, duplicates_removed = deduplicate(passed)

    scored_jobs = [
        score_job(
            job,
            settings=settings,
            skills_config=skills_config,
            exclusions=exclusions,
            candidate_profile=candidate_profile,
            target_titles=target_titles,
        )
        for job in deduped
    ]

    jobs_new = 0
    jobs_updated = 0
    if not dry_run:
        for job in scored_jobs:
            is_new = database.upsert_job(job)
            if is_new:
                jobs_new += 1
            else:
                jobs_updated += 1
        database.finish_run(
            run_id,
            jobs_found=len(all_jobs),
            jobs_new=jobs_new,
            jobs_rejected=len(rejected),
            duplicates_removed=duplicates_removed,
        )

    top_jobs = sorted(scored_jobs, key=lambda j: j.match_score or 0, reverse=True)[:20]

    return SearchRunResult(
        focus=focus,
        run_id=run_id,
        jobs_found=len(all_jobs),
        jobs_new=jobs_new,
        jobs_updated=jobs_updated,
        jobs_rejected=len(rejected),
        duplicates_removed=duplicates_removed,
        failed_sites=failed_sites,
        top_jobs=top_jobs,
    )
