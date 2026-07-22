#!/usr/bin/env python3
"""CLI entry point for the accounting job search system.

Usage:
    python app.py search --focus bookkeeping
    python app.py search --focus staff-accountant
    python app.py search --focus accounts-payable
    python app.py search --focus controller
    python app.py search --focus real-estate
    python app.py search --focus executive-assistant
    python app.py search --focus broad
    python app.py search --focus bookkeeping --dry-run
    python app.py list --status "Apply Immediately" --min-score 80
"""

from __future__ import annotations

import argparse
import logging
import sys

from database.db import JobDatabase
from job_search.query_builder import available_focuses
from job_search.scorer import load_settings
from job_search.search_service import run_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")


def cmd_search(args: argparse.Namespace) -> int:
    result = run_search(args.focus, dry_run=args.dry_run)

    print(f"\nSearch run: focus={result.focus} run_id={result.run_id}")
    print(f"  Jobs found (pre-filter): {result.jobs_found}")
    print(f"  Rejected by filters:     {result.jobs_rejected}")
    print(f"  Duplicates removed:      {result.duplicates_removed}")
    print(f"  New jobs stored:         {result.jobs_new}")
    print(f"  Existing jobs updated:   {result.jobs_updated}")

    if result.failed_sites:
        print("\n  Board failures (other boards still ran):")
        for failure in result.failed_sites:
            print(f"    - {failure.site}: {failure.error}")

    if result.top_jobs:
        print("\n  Top matches this run:")
        for job in result.top_jobs[:10]:
            print(f"    [{job.match_score:>3}] {job.title} @ {job.company} ({job.location}) - {job.job_url}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    settings = load_settings()
    db = JobDatabase(settings.get("database", {}).get("path"))
    rows = db.list_jobs(status=args.status, min_score=args.min_score)
    if not rows:
        print("No jobs found matching those filters.")
        return 0
    for row in rows:
        print(f"[{row['match_score']:>3}] {row['title']} @ {row['company']} - {row['status']} - {row['job_url']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accounting job search CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Run a job search for a focus category")
    search_parser.add_argument(
        "--focus",
        required=True,
        choices=available_focuses(),
        help="Which job title category to search (or 'broad' for all)",
    )
    search_parser.add_argument("--dry-run", action="store_true", help="Search and score but do not write to the database")
    search_parser.set_defaults(func=cmd_search)

    list_parser = subparsers.add_parser("list", help="List stored jobs")
    list_parser.add_argument("--status", default=None, help="Filter by tracker status")
    list_parser.add_argument("--min-score", type=int, default=None, help="Minimum match score")
    list_parser.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        logger.error(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
