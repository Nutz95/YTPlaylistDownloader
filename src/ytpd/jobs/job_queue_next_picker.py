from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus


class JobQueueNextPicker:
    """Pick the next job to run from a creation-ordered snapshot list."""

    def pick(self, jobs: list[JobSnapshot]) -> str | None:
        """Return the oldest queued job id, else the oldest interrupted, else ``None``."""
        queued = self._first_with_status(jobs, JobStatus.QUEUED)
        if queued is not None:
            return queued
        return self._first_with_status(jobs, JobStatus.INTERRUPTED)

    def _first_with_status(
        self,
        jobs: list[JobSnapshot],
        status: JobStatus,
    ) -> str | None:
        for job in jobs:
            if job.status is status:
                return job.job_id
        return None
