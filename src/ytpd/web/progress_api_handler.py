from fastapi.responses import JSONResponse

from ytpd.jobs.job_store import JobStore
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.web.progress_snapshot_codec import ProgressSnapshotCodec


class ProgressApiHandler:
    """HTTP handlers for job progress polling."""

    def __init__(
        self,
        job_store: JobStore,
        calculator: ProgressCalculator,
        codec: ProgressSnapshotCodec,
    ) -> None:
        self._job_store = job_store
        self._calculator = calculator
        self._codec = codec

    async def get_progress(self, job_id: str) -> JSONResponse:
        """Return the latest computed progress for a job."""
        job = self._job_store.get(job_id)
        if job is None:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        snapshot = self._calculator.from_job(job)
        return JSONResponse(content=self._codec.to_payload(snapshot))
