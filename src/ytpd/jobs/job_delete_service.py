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
