import json
from pathlib import Path

from sqlalchemy import create_engine, delete, select
from sqlalchemy.dialects.sqlite import insert

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.jobs.job_snapshot_codec import JobSnapshotCodec
from ytpd.jobs.jobs_checkpoint_table import JobsCheckpointTable


class SqliteJobCheckpointStore:
    """SQLite-backed checkpoint store for job snapshots (SQLAlchemy Core)."""

    def __init__(self, database_path: Path) -> None:
        self._codec = JobSnapshotCodec()
        self._table = JobsCheckpointTable()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{database_path.as_posix()}")
        self._table.create_all(self._engine)

    def save(self, snapshot: JobSnapshot) -> None:
        """Upsert one job snapshot."""
        payload = self._codec.to_payload(snapshot)
        statement = insert(self._table.table).values(
            job_id=snapshot.job_id,
            payload_json=json.dumps(payload),
        )
        upsert = statement.on_conflict_do_update(
            index_elements=[self._table.table.c.job_id],
            set_={"payload_json": statement.excluded.payload_json},
        )
        with self._engine.begin() as connection:
            connection.execute(upsert)

    def load(self, job_id: str) -> JobSnapshot | None:
        """Return a job by id when present."""
        statement = (
            select(self._table.table.c.payload_json)
            .where(self._table.table.c.job_id == job_id)
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).fetchone()
        if row is None:
            return None
        return self._codec.from_json_text(row.payload_json)

    def list_jobs(self) -> list[JobSnapshot]:
        """Return all stored jobs ordered by insertion rowid."""
        statement = select(self._table.table.c.payload_json).order_by(
            self._table.table.c.job_id.asc()
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).fetchall()
        return [self._codec.from_json_text(row.payload_json) for row in rows]

    def delete(self, job_id: str) -> bool:
        """Remove one job by id. Return True when a row was deleted."""
        statement = delete(self._table.table).where(
            self._table.table.c.job_id == job_id
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return int(result.rowcount or 0) > 0
