import json
import sqlite3
from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.jobs.job_snapshot_codec import JobSnapshotCodec


class SqliteJobCheckpointStore:
    """SQLite-backed checkpoint store for job snapshots."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._codec = JobSnapshotCodec()
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save(self, snapshot: JobSnapshot) -> None:
        """Upsert one job snapshot."""
        payload = self._codec.to_payload(snapshot)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO jobs (job_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(job_id) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (snapshot.job_id, json.dumps(payload)),
            )
            connection.commit()

    def load(self, job_id: str) -> JobSnapshot | None:
        """Return a job by id when present."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT payload_json FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return self._codec.from_json_text(row[0])

    def list_jobs(self) -> list[JobSnapshot]:
        """Return all stored jobs ordered by rowid."""
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT payload_json FROM jobs ORDER BY rowid ASC"
            ).fetchall()
        return [self._codec.from_json_text(row[0]) for row in rows]

    def _initialize(self) -> None:
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.commit()
