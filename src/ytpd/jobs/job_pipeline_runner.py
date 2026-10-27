import threading
from dataclasses import replace

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_cancel_finalizer import JobCancelFinalizer
from ytpd.jobs.job_orchestrator import JobOrchestrator
from ytpd.jobs.job_store import JobStore
from ytpd.ports.request_aborter import RequestAborter


class JobPipelineRunner:
    """Run the job orchestrator on a background thread for non-blocking HTTP."""

    def __init__(
        self,
        job_store: JobStore,
        orchestrator: JobOrchestrator,
        request_aborter: RequestAborter,
        cancel_finalizer: JobCancelFinalizer,
    ) -> None:
        self._job_store = job_store
        self._orchestrator = orchestrator
        self._request_aborter = request_aborter
        self._cancel_finalizer = cancel_finalizer
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._active_job_id: str | None = None

    def start(self, job_id: str) -> JobSnapshot:
        """Mark the job running and start the pipeline in the background."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise InvalidJobError("a pipeline is already running")
            job = self._job_store.get(job_id)
            if job is None:
                raise InvalidJobError("job not found")
            started = self._job_store.save(
                replace(
                    job,
                    status=JobStatus.RUNNING,
                    pipeline_stage=None,
                    error_message=None,
                )
            )
            self._active_job_id = job_id
            self._thread = threading.Thread(
                target=self._run_safe,
                args=(job_id,),
                name=f"ytpd-pipeline-{job_id[:8]}",
                daemon=True,
            )
            self._thread.start()
            return started

    def is_busy(self) -> bool:
        """True when a background pipeline thread is still alive."""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def active_job_id(self) -> str | None:
        """Return the job id currently running in the background, if any."""
        with self._lock:
            return self._active_job_id

    def cancel(self, job_id: str | None = None) -> JobSnapshot | None:
        """Cancel remaining work, abort HTTP, and persist CANCELLED immediately."""
        self._orchestrator.cancel()
        self._request_aborter.abort()
        with self._lock:
            target = job_id if job_id is not None else self._active_job_id
        if target is None:
            return None
        return self._cancel_finalizer.finalize(target)

    def _run_safe(self, job_id: str) -> None:
        try:
            result = self._orchestrator.run_job(job_id)
            if result.cancelled:
                self._cancel_finalizer.finalize(job_id)
        except Exception as error:
            self._mark_failed(job_id, str(error))
        finally:
            with self._lock:
                self._active_job_id = None

    def _mark_failed(self, job_id: str, message: str) -> None:
        job = self._job_store.get(job_id)
        if job is None:
            return
        if job.status is JobStatus.CANCELLED:
            return
        self._job_store.save(
            replace(
                job,
                status=JobStatus.FAILED,
                pipeline_stage=None,
                error_message=message,
            )
        )
