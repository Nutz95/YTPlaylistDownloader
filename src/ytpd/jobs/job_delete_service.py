import shutil

from ytpd.domain.job_status import JobStatus
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.active_job_id_reader import ActiveJobIdReader


class JobDeleteService:
    """Remove a finished job checkpoint and its work directory."""

    def __init__(
        self,
        job_store: JobStore,
        active_job_reader: ActiveJobIdReader,
        paths: TrackArtifactPaths,
    ) -> None:
        self._job_store = job_store
        self._active_job_reader = active_job_reader
        self._paths = paths

    def delete(self, job_id: str) -> None:
        """Delete ``job_id`` when it is not actively running."""
        job = self._job_store.get(job_id)
        if job is None:
            raise InvalidJobError("job not found")
        if job.status is JobStatus.RUNNING:
            raise InvalidJobError("cannot delete a running job")
        if self._active_job_reader.active_job_id() == job_id:
            raise InvalidJobError("cannot delete a running job")
        if not self._job_store.delete(job_id):
            raise InvalidJobError("job not found")
        work_dir = self._paths.job_work_dir(job)
        if work_dir.is_dir():
            shutil.rmtree(work_dir)

    def delete_completed(self) -> list[str]:
        """Delete every COMPLETED job; skip ones that cannot be deleted now."""
        deleted_job_ids: list[str] = []
        for job in self._job_store.list_jobs():
            if not self._try_delete_completed(job.job_id):
                continue
            deleted_job_ids.append(job.job_id)
        return deleted_job_ids

    def _try_delete_completed(self, job_id: str) -> bool:
        latest = self._job_store.get(job_id)
        if latest is None or latest.status is not JobStatus.COMPLETED:
            return False
        try:
            self.delete(job_id)
        except InvalidJobError:
            return False
        return True
