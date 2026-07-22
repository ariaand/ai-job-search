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

# JobSpy logs per-board failures (403s, rate limits, etc.) through its own
# loggers (e.g. "JobSpy:ZipRecruiter") instead of raising - scrape_jobs()
# returns an empty/partial DataFrame and swallows the error internally. A
# bare try/except around scrape_jobs() therefore never sees these failures.
# _CapturingHandler intercepts them via the root logger so a board that
# silently returned nothing still gets recorded as a failed source.
_JOBSPY_LOGGER_NAMES = {
    "indeed": "JobSpy:Indeed",
    "linkedin": "JobSpy:LinkedIn",
    "zip_recruiter": "JobSpy:ZipRecruiter",
    "glassdoor": "JobSpy:Glassdoor",
    "google": "JobSpy:Google",
}


class _CapturingHandler(logging.Handler):
    """Attached directly to JobSpy's own per-site logger (see module docstring
    above _JOBSPY_LOGGER_NAMES) rather than the root logger: JobSpy's loggers
    set `propagate = False` (they log via their own handler, which is why the
    messages print even though nothing reaches the root logger's handlers),
    so a handler only attached to root would silently miss every one of them."""

    def __init__(self, level: int = logging.WARNING) -> None:
        super().__init__(level=level)
        self.records: list[tuple[str, str]] = []  # (logger_name, message)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append((record.name, record.getMessage()))

    def messages(self) -> list[str]:
        return [msg for _name, msg in self.records]


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

                capture = _CapturingHandler()
                jobspy_logger = logging.getLogger(_JOBSPY_LOGGER_NAMES.get(site, f"JobSpy:{site}"))
                jobspy_logger.addHandler(capture)
                try:
                    df = scrape_jobs(**kwargs)
                finally:
                    jobspy_logger.removeHandler(capture)

                jobs = [] if df is None or df.empty else df.to_dict(orient="records")
                board_errors = capture.messages()

                if not jobs and board_errors:
                    # scrape_jobs() didn't raise, but this board logged a
                    # failure and delivered nothing - treat it as a failed
                    # source (e.g. anti-bot 403/429) rather than a silent 0.
                    last_error = "; ".join(dict.fromkeys(board_errors))  # de-dup, preserve order
                    logger.warning("JobSpy site=%s attempt=%s reported errors: %s", site, attempt, last_error)
                    if attempt < self.max_retries_per_site:
                        time.sleep(min(2**attempt, 10))
                    continue

                return BoardResult(site=site, jobs=jobs, attempts=attempt)

            except Exception as exc:  # noqa: BLE001 - any board failure must not crash the run
                last_error = str(exc)
                logger.warning("JobSpy site=%s attempt=%s failed: %s", site, attempt, last_error)
                if attempt < self.max_retries_per_site:
                    time.sleep(min(2 ** attempt, 10))  # backoff, capped at 10s

        return BoardResult(site=site, error=last_error or "unknown error", attempts=self.max_retries_per_site)
