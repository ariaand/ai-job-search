"""SQLite schema definitions.

Column types and constraints are kept to the ANSI-SQL subset SQLite and
PostgreSQL both support (TEXT/INTEGER/REAL/BOOLEAN, no SQLite-only pragmas
in the DDL itself) so `database/db.py` can be pointed at Postgres later by
swapping the connection layer without rewriting these statements.
"""

from __future__ import annotations

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id                      TEXT PRIMARY KEY,
    source                      TEXT NOT NULL,
    title                       TEXT NOT NULL,
    company                     TEXT NOT NULL,
    location                    TEXT,
    remote_status               TEXT,
    employment_type             TEXT,
    salary_min                  REAL,
    salary_max                  REAL,
    salary_interval             TEXT,
    date_posted                 TEXT,
    date_discovered             TEXT NOT NULL,
    job_url                     TEXT,
    direct_application_url      TEXT,
    description                 TEXT,
    required_skills             TEXT,
    preferred_skills             TEXT,
    cpa_required                BOOLEAN DEFAULT 0,
    years_experience_required   INTEGER,
    match_score                 INTEGER,
    match_explanation           TEXT,
    red_flags                   TEXT,
    status                      TEXT NOT NULL DEFAULT 'New',
    notes                       TEXT,
    date_applied                TEXT,
    follow_up_date              TEXT,
    interview_date              TEXT,
    rejection_date               TEXT,
    offer_status                TEXT
);
"""

CREATE_SEARCH_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS search_runs (
    run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at        TEXT NOT NULL,
    finished_at       TEXT,
    focus             TEXT,
    sites_requested   TEXT,
    jobs_found        INTEGER DEFAULT 0,
    jobs_new          INTEGER DEFAULT 0,
    jobs_rejected     INTEGER DEFAULT 0,
    duplicates_removed INTEGER DEFAULT 0
);
"""

CREATE_FAILED_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS failed_sources (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id     INTEGER NOT NULL REFERENCES search_runs(run_id),
    site       TEXT NOT NULL,
    error      TEXT,
    attempts   INTEGER,
    occurred_at TEXT NOT NULL
);
"""

ALL_STATEMENTS = [CREATE_JOBS_TABLE, CREATE_SEARCH_RUNS_TABLE, CREATE_FAILED_SOURCES_TABLE]
