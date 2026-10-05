import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from backend.config import settings
from backend.jobs.models import JobRecord, JobStatus

class JobRepository:
    """SQLite repository for job snapshots, lifecycle state, and progress."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path if db_path is not None else settings.db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    spec_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0.0,
                    row_count INTEGER NOT NULL,
                    is_preview INTEGER NOT NULL DEFAULT 0,
                    use_ollama INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT,
                    artifact_dir TEXT NOT NULL
                )
                """
            )
            # Reconcile interrupted jobs
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, error_message = ?, updated_at = ?
                WHERE status IN (?, ?)
                """,
                (JobStatus.FAILED.value, "Process interrupted on server restart.", now, JobStatus.RUNNING.value, JobStatus.CANCELLING.value),
            )
            conn.commit()

    def create_job(self, record: JobRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, spec_json, status, progress, row_count,
                    is_preview, use_ollama, created_at, updated_at,
                    completed_at, error_message, artifact_dir
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.spec_json,
                    record.status.value,
                    record.progress,
                    record.row_count,
                    1 if record.is_preview else 0,
                    1 if record.use_ollama else 0,
                    record.created_at,
                    record.updated_at,
                    record.completed_at,
                    record.error_message,
                    record.artifact_dir,
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return JobRecord(
                id=row["id"],
                spec_json=row["spec_json"],
                status=JobStatus(row["status"]),
                progress=row["progress"],
                row_count=row["row_count"],
                is_preview=bool(row["is_preview"]),
                use_ollama=bool(row["use_ollama"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                completed_at=row["completed_at"],
                error_message=row["error_message"],
                artifact_dir=row["artifact_dir"],
            )

    def update_progress(self, job_id: str, progress: float) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET progress = ?, updated_at = ? WHERE id = ?",
                (progress, now, job_id),
            )
            conn.commit()

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: str | None = None,
        progress: float | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED) else None

        with self._get_connection() as conn:
            if progress is not None:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?, error_message = ?, progress = ?, updated_at = ?, completed_at = COALESCE(completed_at, ?)
                    WHERE id = ?
                    """,
                    (status.value, error_message, progress, now, completed_at, job_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?, error_message = ?, updated_at = ?, completed_at = COALESCE(completed_at, ?)
                    WHERE id = ?
                    """,
                    (status.value, error_message, now, completed_at, job_id),
                )
            conn.commit()

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [
                JobRecord(
                    id=r["id"],
                    spec_json=r["spec_json"],
                    status=JobStatus(r["status"]),
                    progress=r["progress"],
                    row_count=r["row_count"],
                    is_preview=bool(r["is_preview"]),
                    use_ollama=bool(r["use_ollama"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    completed_at=r["completed_at"],
                    error_message=r["error_message"],
                    artifact_dir=r["artifact_dir"],
                )
                for r in rows
            ]
