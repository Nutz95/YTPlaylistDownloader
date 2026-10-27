from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.invalid_job_error import InvalidJobError


class RecordingDownloadTranscodeCoordinator:
    """Record when media pipeline runs; return the current job snapshot."""

    def __init__(self, job_store: JobStore, events: list[str]) -> None:
        self._job_store = job_store
        self._events = events

    def run(self, job_id: str) -> JobSnapshot:
        """Append a media event and return the stored job."""
        self._events.append("media")
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        return job
