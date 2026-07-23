"""Builds JobSpy search terms from config/job_titles.yaml.

One `Query` per job title, each suffixed with a category-appropriate keyword
hint (e.g. "staff accountant" -> "staff accountant excel reconciliation"),
mirroring the spec's own example queries:

    "remote bookkeeper" "QuickBooks Online"
    "staff accountant" remote Excel reconciliation
    "accounts payable specialist" remote
    "client accounting services" remote QBO
    "property accountant" remote
    "virtual executive assistant" bookkeeping remote

Exclusion terms (sales, insurance, MLM, etc.) are deliberately NOT baked
into the search string here - board query-operator support is inconsistent,
so exclusion is handled uniformly post-scrape by job_search/filters.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

# Category -> keyword hint appended to every title in that category, to
# disambiguate broad titles without exploding into a full title x skill
# cross product. Kept short and representative of config/skills.yaml.
CATEGORY_KEYWORD_HINTS: dict[str, str] = {
    "bookkeeping": "QuickBooks Online",
    "staff-accountant": "Excel reconciliation",
    "accounts-payable": "",
    "controller": "",
    "real-estate": "property accounting",
    "client-accounting": "QBO",
    "executive-assistant": "bookkeeping",
}


@dataclass(frozen=True)
class Query:
    focus: str
    title: str
    search_term: str
    google_search_term: str


def load_job_titles(path: Optional[Path] = None) -> dict[str, list[str]]:
    data = yaml.safe_load(open(path or CONFIG_DIR / "job_titles.yaml", "r", encoding="utf-8")) or {}
    return {k: v for k, v in data.items() if isinstance(v, list)}


def available_focuses(job_titles: Optional[dict[str, list[str]]] = None) -> list[str]:
    titles = job_titles or load_job_titles()
    return sorted(titles.keys()) + ["broad"]


def build_queries(
    focus: str,
    job_titles: Optional[dict[str, list[str]]] = None,
    category_keyword_hints: Optional[dict[str, str]] = None,
) -> list[Query]:
    """Build one Query per job title for the given focus category.

    `focus="broad"` runs every title in every category. An unknown focus
    raises ValueError listing valid choices, so CLI/dashboard callers can
    surface a clear error instead of silently returning nothing.
    """
    titles_by_focus = job_titles or load_job_titles()
    hints = category_keyword_hints or CATEGORY_KEYWORD_HINTS

    if focus == "broad":
        selected: dict[str, list[str]] = titles_by_focus
    elif focus in titles_by_focus:
        selected = {focus: titles_by_focus[focus]}
    else:
        raise ValueError(
            f"Unknown focus '{focus}'. Valid options: {', '.join(available_focuses(titles_by_focus))}"
        )

    queries: list[Query] = []
    for category, titles in selected.items():
        hint = hints.get(category, "")
        for title in titles:
            search_term = f"{title} {hint}".strip()
            google_term = f"{search_term} jobs in the United States".strip()
            queries.append(
                Query(focus=category, title=title, search_term=search_term, google_search_term=google_term)
            )
    return queries
