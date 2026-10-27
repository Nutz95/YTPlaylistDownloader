from ytpd.domain.job_resume_plan import JobResumePlan
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_resume_planner import JobResumePlanner
from ytpd.jobs.job_store import JobStore

_RESUMABLE = frozenset(
    {
        JobStatus.QUEUED,
        JobStatus.PAUSED,
        JobStatus.INTERRUPTED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }
)


class JobResumeService:
    """Crash recovery and explicit resume commands that mutate job status."""

    def __init__(self, job_store: JobStore, planner: JobResumePlanner) -> None:
        self._job_store = job_store
        self._planner = planner

    def mark_stale_running_interrupted(self) -> list[JobSnapshot]:
        """Rewrite leftover RUNNING jobs as INTERRUPTED after a process restart."""
        updated: list[JobSnapshot] = []
        for job in self._job_store.list_jobs():
            if job.status is not JobStatus.RUNNING:
                continue
            updated.append(self._job_store.save(job.with_status(JobStatus.INTERRUPTED)))
        return updated

    def resume_job(self, job_id: str) -> JobResumePlan:
        """Mark a resumable job RUNNING and return its plan."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if job.status is JobStatus.RUNNING:
            return self._planner.plan(job)
        if job.status not in _RESUMABLE:
            raise InvalidJobError(
                f"job status {job.status.value} is not resumable"
            )
        plan = self._planner.plan(job)
        if not plan.is_actionable():
            raise InvalidJobError("job has no pending resume work")
        self._job_store.save(job.with_status(JobStatus.RUNNING))
        return plan
