from uuid import uuid4

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.ports.job_checkpoint_store import JobCheckpointStore


class JobStore:
    """Create and query jobs through the checkpoint store."""

    def __init__(self, checkpoint_store: JobCheckpointStore) -> None:
        self._checkpoint_store = checkpoint_store

    def create(self, source_url: str) -> JobSnapshot:
        """Create a queued job for ``source_url`` and persist it."""
        cleaned = source_url.strip()
        if cleaned == "":
            raise InvalidJobError("source_url must be a non-empty string")
        snapshot = JobSnapshot(
            job_id=str(uuid4()),
            source_url=cleaned,
            source_kind=SourceKind.UNKNOWN,
            status=JobStatus.QUEUED,
            tracks=[],
            error_message=None,
        )
        self._checkpoint_store.save(snapshot)
        return snapshot

    def get(self, job_id: str) -> JobSnapshot | None:
        """Return one job when present."""
        return self._checkpoint_store.load(job_id)

    def list_jobs(self) -> list[JobSnapshot]:
        """Return all persisted jobs."""
        return self._checkpoint_store.list_jobs()

    def save(self, snapshot: JobSnapshot) -> JobSnapshot:
        """Persist an updated snapshot and return it."""
        self._checkpoint_store.save(snapshot)
        return snapshot
