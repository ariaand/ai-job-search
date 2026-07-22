"""SQLite access layer for stored jobs, search runs, and failed-source tracking.

Kept deliberately thin (plain sqlite3 + parameterized SQL, no ORM) so a
future move to PostgreSQL only requires swapping `_connect()` and the
AUTOINCREMENT keyword in schema.py for a SERIAL/IDENTITY column.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from database.schema import ALL_STATEMENTS
from job_search.models import Job

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "database" / "jobs.db"


class JobDatabase:
    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        if not db_path:
            self.db_path = DEFAULT_DB_PATH
        else:
            path = Path(db_path)
            # Relative paths (e.g. "database/jobs.db" from settings.yaml) must
            # anchor to the repo root, not the caller's CWD - otherwise the
            # CLI and the Streamlit dashboard (launched from different
            # working directories) silently write to two different files.
            self.db_path = path if path.is_absolute() else REPO_ROOT / path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            for statement in ALL_STATEMENTS:
                conn.execute(statement)

    # --- Jobs ---

    def upsert_job(self, job: Job) -> bool:
        """Insert a new job, or update an existing one's discovery-time fields
        (score, description, etc.) while preserving user-set tracking fields
        (status, notes, date_applied, ...) if the job already exists.
        Returns True if this was a new insert, False if it updated an
        existing row."""
        existing = self.get_job(job.job_id)
        with self._connect() as conn:
            if existing is None:
                data = job.to_dict()
                columns = ", ".join(data.keys())
                placeholders = ", ".join(f":{k}" for k in data.keys())
                conn.execute(f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", data)
                return True

            # Preserve user-managed tracking fields; refresh discovery/scoring fields.
            data = job.to_dict()
            for preserved in (
                "status",
                "notes",
                "date_applied",
                "follow_up_date",
                "interview_date",
                "rejection_date",
                "offer_status",
            ):
                data[preserved] = existing[preserved]
            set_clause = ", ".join(f"{k} = :{k}" for k in data.keys() if k != "job_id")
            conn.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = :job_id", data)
            return False

    def get_job(self, job_id: str) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            return row

    def list_jobs(
        self,
        status: Optional[str] = None,
        min_score: Optional[int] = None,
        order_by: str = "match_score DESC",
    ) -> list[sqlite3.Row]:
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if min_score is not None:
            query += " AND match_score >= ?"
            params.append(min_score)
        query += f" ORDER BY {order_by}"
        with self._connect() as conn:
            return conn.execute(query, params).fetchall()

    def update_status(self, job_id: str, status: str, **date_fields: str) -> None:
        fields = {"status": status, **date_fields}
        set_clause = ", ".join(f"{k} = :{k}" for k in fields.keys())
        fields["job_id"] = job_id
        with self._connect() as conn:
            conn.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = :job_id", fields)

    # --- Search run history ---

    def start_run(self, focus: str, sites_requested: list[str]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO search_runs (started_at, focus, sites_requested) VALUES (?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), focus, ",".join(sites_requested)),
            )
            return cursor.lastrowid

    def finish_run(
        self, run_id: int, jobs_found: int, jobs_new: int, jobs_rejected: int, duplicates_removed: int
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE search_runs SET finished_at = ?, jobs_found = ?, jobs_new = ?,
                   jobs_rejected = ?, duplicates_removed = ? WHERE run_id = ?""",
                (
                    datetime.now(timezone.utc).isoformat(),
                    jobs_found,
                    jobs_new,
                    jobs_rejected,
                    duplicates_removed,
                    run_id,
                ),
            )

    def record_failed_source(self, run_id: int, site: str, error: str, attempts: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO failed_sources (run_id, site, error, attempts, occurred_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, site, error, attempts, datetime.now(timezone.utc).isoformat()),
            )

    def recent_runs(self, limit: int = 20) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM search_runs ORDER BY run_id DESC LIMIT ?", (limit,)
            ).fetchall()
