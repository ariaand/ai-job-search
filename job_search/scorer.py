"""Transparent 0-100 match scorer.

Scoring weights/deductions/rating bands live in config/settings.yaml so they
can be tuned without touching code. `score_job` mutates and returns the same
Job with match_score, match_explanation, red_flags, required_skills, and
preferred_skills populated - callers persist the returned Job as-is.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from job_search.models import Job

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class ScoreBreakdown:
    score: int
    rating: str
    explanation: str
    matching_skills: list[str]
    missing_skills: list[str]
    red_flags: list[str]
    recommendation: str


def load_settings(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(open(path or CONFIG_DIR / "settings.yaml", "r", encoding="utf-8")) or {}


def load_skills_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(open(path or CONFIG_DIR / "skills.yaml", "r", encoding="utf-8")) or {}


def load_exclusions(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(open(path or CONFIG_DIR / "exclusions.yaml", "r", encoding="utf-8")) or {}


def load_candidate_profile(path: Optional[Path] = None) -> dict:
    settings = load_settings()
    profile_path = Path(path or settings.get("candidate_profile_path", "config/candidate_profile.yaml"))
    if not profile_path.is_absolute():
        profile_path = CONFIG_DIR.parent / profile_path
    return yaml.safe_load(open(profile_path, "r", encoding="utf-8")) or {}


def _rating_for(score: int, bands: list[dict]) -> str:
    for band in bands:
        if band["min"] <= score <= band["max"]:
            return band["label"]
    return "Low Priority"


def _recommendation_for(rating: str) -> str:
    return {
        "Apply Immediately": "Apply now - excellent match on every major criterion.",
        "Strong Match": "Strong fit - apply soon.",
        "Good Match": "Good fit - worth applying, review missing skills first.",
        "Review Carefully": "Mixed fit - read the full posting before deciding.",
        "Low Priority": "Weak fit - only pursue if pipeline is thin.",
    }.get(rating, "Review before applying.")


def score_job(
    job: Job,
    settings: Optional[dict] = None,
    skills_config: Optional[dict] = None,
    exclusions: Optional[dict] = None,
    candidate_profile: Optional[dict] = None,
    target_titles: Optional[list[str]] = None,
) -> Job:
    """Scores `job` in place and returns it. `target_titles` should be the
    title list for the focus category the job was searched under (used for
    title-match scoring); pass None to skip title-match points."""

    settings = settings if settings is not None else load_settings()
    skills_config = skills_config if skills_config is not None else load_skills_config()
    exclusions = exclusions if exclusions is not None else load_exclusions()
    candidate_profile = candidate_profile if candidate_profile is not None else load_candidate_profile()

    weights = settings["scoring"]["weights"]
    deductions = settings["scoring"]["deductions"]
    bands = settings["scoring"]["rating_bands"]
    max_age_days = settings.get("filters", {}).get("max_posting_age_days", 14)
    recent_days = settings.get("search", {}).get("recent_priority_days", 7)

    blob = f"{job.title}\n{job.description}".lower()
    points = 0
    explanation_lines: list[str] = []
    red_flags: list[str] = list(job.red_flags)
    matching_skills: list[str] = []
    missing_skills: list[str] = []

    # --- Additive points ---
    if job.remote_status == "remote":
        points += weights["remote"]
        explanation_lines.append(f"+{weights['remote']} remote")

    if "flexible" in blob or "flex schedule" in blob:
        points += weights["flexible_schedule"]
        explanation_lines.append(f"+{weights['flexible_schedule']} flexible schedule mentioned")

    if target_titles:
        title_lower = job.title.lower()
        if any(t.lower() in title_lower or title_lower in t.lower() for t in target_titles):
            points += weights["title_match"]
            explanation_lines.append(f"+{weights['title_match']} title matches target role")

    software_keywords = skills_config.get("software", [])
    software_hits = [kw for kw in software_keywords if kw.lower() in blob]
    if software_hits:
        points += weights["software_match"]
        matching_skills.extend(software_hits)
        explanation_lines.append(f"+{weights['software_match']} software match: {', '.join(software_hits)}")
    else:
        missing_skills.extend(software_keywords[:3])

    process_keywords = skills_config.get("accounting_process", [])
    profile_skills_lower = {s.lower() for s in candidate_profile.get("skills", [])}
    process_hits = [kw for kw in process_keywords if kw.lower() in blob]
    experience_overlap = process_hits or [kw for kw in process_keywords if kw.lower() in profile_skills_lower]
    if experience_overlap:
        points += weights["accounting_experience_match"]
        matching_skills.extend(process_hits)
        explanation_lines.append(
            f"+{weights['accounting_experience_match']} accounting experience match: {', '.join(process_hits) or 'profile overlap'}"
        )

    excel_recon_hit = any(kw in blob for kw in ("excel", "reconciliation", "reconciliations"))
    if excel_recon_hit:
        points += weights["excel_reconciliation_match"]
        explanation_lines.append(f"+{weights['excel_reconciliation_match']} Excel/reconciliation match")

    preferred_types = candidate_profile.get("preferred_work", {}).get("employment_types_preferred", [])
    employment_type_map = {"fulltime_w2": "fulltime", "parttime_w2": "parttime", "contract": "contract"}
    preferred_simple = {employment_type_map.get(t, t) for t in preferred_types}
    if job.employment_type in preferred_simple:
        points += weights["preferred_employment_type"]
        explanation_lines.append(f"+{weights['preferred_employment_type']} preferred employment type")

    if job.salary_min or job.salary_max:
        points += weights["salary_listed"]
        explanation_lines.append(f"+{weights['salary_listed']} salary listed")

    days_old = _days_old(job.date_posted)
    if days_old is not None and days_old <= recent_days:
        points += weights["recency_bonus_days"]
        explanation_lines.append(f"+{weights['recency_bonus_days']} posted within {recent_days} days")

    if job.direct_application_url:
        points += weights["direct_employer_application"]
        explanation_lines.append(f"+{weights['direct_employer_application']} direct employer application")

    # --- Deductions ---
    cpa_mandatory_hit = any(
        kw in blob for kw in ("cpa required", "must have active cpa", "active cpa license required")
    )
    if cpa_mandatory_hit:
        points -= deductions["cpa_mandatory"]
        job.cpa_required = True
        red_flags.append("CPA license mandatory")
        explanation_lines.append(f"-{deductions['cpa_mandatory']} CPA mandatory")
    elif any(kw in blob for kw in ("cpa preferred", "cpa a plus", "cpa is a plus")):
        red_flags.append("CPA preferred (not mandatory)")

    if job.remote_status == "hybrid":
        points -= deductions["hybrid_only"]
        explanation_lines.append(f"-{deductions['hybrid_only']} hybrid-only")

    if not (job.salary_min or job.salary_max):
        points -= deductions["missing_salary"]
        explanation_lines.append(f"-{deductions['missing_salary']} salary not listed")

    if days_old is not None and days_old > max_age_days:
        points -= deductions["stale_posting"]
        red_flags.append(f"Posting is {days_old} days old (> {max_age_days})")
        explanation_lines.append(f"-{deductions['stale_posting']} stale posting")

    for rule in exclusions.get("penalty", []):
        if any(kw.lower() in blob for kw in rule.get("keywords", [])):
            points -= rule["points"]
            red_flags.append(rule["reason"])
            explanation_lines.append(f"-{rule['points']} {rule['reason']}")

    for rule in exclusions.get("flag", []):
        if any(kw.lower() in blob for kw in rule.get("keywords", [])):
            if rule["reason"] not in red_flags:
                red_flags.append(rule["reason"])

    score = max(0, min(100, points))
    rating = _rating_for(score, bands)

    job.match_score = score
    job.match_explanation = "; ".join(explanation_lines) if explanation_lines else "No scoring signals matched."
    job.red_flags = red_flags
    job.required_skills = process_hits
    job.preferred_skills = software_hits
    job.notes = job.notes or ""

    return job


def get_score_breakdown(job: Job) -> ScoreBreakdown:
    """Convenience accessor for dashboard/CLI display after score_job has run."""
    settings = load_settings()
    bands = settings["scoring"]["rating_bands"]
    rating = _rating_for(job.match_score or 0, bands)
    return ScoreBreakdown(
        score=job.match_score or 0,
        rating=rating,
        explanation=job.match_explanation,
        matching_skills=job.preferred_skills,
        missing_skills=[],
        red_flags=job.red_flags,
        recommendation=_recommendation_for(rating),
    )


def _days_old(date_posted: Optional[str]) -> Optional[int]:
    if not date_posted:
        return None
    from datetime import date, datetime

    try:
        parsed = datetime.fromisoformat(date_posted).date() if "T" in date_posted else date.fromisoformat(date_posted)
    except (ValueError, TypeError):
        return None
    return (date.today() - parsed).days
