"""Thin wrapper around python-jobspy (`from jobspy import scrape_jobs`).

Runs one board at a time so a failure, rate limit, or empty result on one
board never stops the others. JobSpy is used as a dependency (`pip install
-U python-jobspy`) and never vendored/rebuilt here, so it keeps receiving
upstream updates.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class BoardResult:
    site: str
    jobs: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    attempts: int = 0

    @property
    def ok(self) -> bool:
        return self.error is None


class JobSpyClient:
    """Runs JobSpy per-site with retries and isolates failures per board."""

    def __init__(
        self,
        results_wanted: int = 50,
        hours_old: int = 336,
        country_indeed: str = "USA",
        max_retries_per_site: int = 2,
        site_timeout_seconds: int = 60,
    ) -> None:
        self.results_wanted = results_wanted
        self.hours_old = hours_old
        self.country_indeed = country_indeed
        self.max_retries_per_site = max_retries_per_site
        self.site_timeout_seconds = site_timeout_seconds

    def search(
        self,
        sites: list[str],
        search_term: str,
        location: str = "United States",
        is_remote: bool = True,
        google_search_term: Optional[str] = None,
    ) -> list[BoardResult]:
        """Search each site independently. Returns one BoardResult per site,
        including failed ones — callers decide whether to surface errors."""

        results: list[BoardResult] = []
        for site in sites:
            results.append(
                self._search_one_site(
                    site=site,
                    search_term=search_term,
                    location=location,
                    is_remote=is_remote,
                    google_search_term=google_search_term,
                )
            )
        return results

    def _search_one_site(
        self,
        site: str,
        search_term: str,
        location: str,
        is_remote: bool,
        google_search_term: Optional[str],
    ) -> BoardResult:
        last_error: Optional[str] = None

        for attempt in range(1, self.max_retries_per_site + 1):
            try:
                from jobspy import scrape_jobs  # deferred import: optional dependency
            except ImportError as exc:
                return BoardResult(
                    site=site,
                    error=f"python-jobspy not installed ({exc}). Run: pip install -U python-jobspy",
                    attempts=attempt,
                )

            try:
                kwargs: dict[str, Any] = dict(
                    site_name=[site],
                    search_term=search_term,
                    location=location,
                    results_wanted=self.results_wanted,
                    hours_old=self.hours_old,
                    country_indeed=self.country_indeed,
                    is_remote=is_remote,
                )
                if site == "google":
                    kwargs["google_search_term"] = google_search_term or f"{search_term} jobs in the United States"

                df = scrape_jobs(**kwargs)
                jobs = [] if df is None or df.empty else df.to_dict(orient="records")
                return BoardResult(site=site, jobs=jobs, attempts=attempt)

            except Exception as exc:  # noqa: BLE001 - any board failure must not crash the run
                last_error = str(exc)
                logger.warning("JobSpy site=%s attempt=%s failed: %s", site, attempt, last_error)
                if attempt < self.max_retries_per_site:
                    time.sleep(min(2 ** attempt, 10))  # backoff, capped at 10s

        return BoardResult(site=site, error=last_error or "unknown error", attempts=self.max_retries_per_site)
