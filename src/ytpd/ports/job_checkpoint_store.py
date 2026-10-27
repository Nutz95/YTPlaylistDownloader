from typing import Protocol

from ytpd.domain.job_snapshot import JobSnapshot


class JobCheckpointStore(Protocol):
    """Persist and reload job snapshots across process restarts."""

    def save(self, snapshot: JobSnapshot) -> None:
        """Upsert one job snapshot."""

    def load(self, job_id: str) -> JobSnapshot | None:
        """Return a job by id when present."""

    def list_jobs(self) -> list[JobSnapshot]:
        """Return all stored jobs ordered by creation time when available."""

    def delete(self, job_id: str) -> bool:
        """Remove one job by id. Return True when a row was deleted."""
