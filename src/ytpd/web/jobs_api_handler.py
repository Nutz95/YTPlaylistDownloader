from collections.abc import Mapping

from fastapi import Request
from fastapi.responses import JSONResponse

from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_resume_plan_codec import JobResumePlanCodec
from ytpd.jobs.job_resume_service import JobResumeService
from ytpd.jobs.job_snapshot_codec import JobSnapshotCodec
from ytpd.jobs.job_store import JobStore


class JobsApiHandler:
    """HTTP handlers for creating, reading, resolving, and resuming jobs."""

    def __init__(
        self,
        job_store: JobStore,
        resume_service: JobResumeService,
        resolve_service: JobResolveService,
    ) -> None:
        self._job_store = job_store
        self._resume_service = resume_service
        self._resolve_service = resolve_service
        self._codec = JobSnapshotCodec()
        self._resume_codec = JobResumePlanCodec()

    async def create_job(self, request: Request) -> JSONResponse:
        """Create a queued job from a JSON ``url`` field."""
        body = await request.json()
        if not isinstance(body, Mapping):
            return JSONResponse(
                status_code=400,
                content={"error": "JSON body must be an object"},
            )
        raw_url = body.get("url")
        if not isinstance(raw_url, str):
            return JSONResponse(
                status_code=400,
                content={"error": "url must be a non-empty string"},
            )
        try:
            snapshot = self._job_store.create(raw_url)
        except InvalidJobError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})
        return JSONResponse(
            status_code=201,
            content=self._codec.to_payload(snapshot),
        )

    async def list_jobs(self) -> JSONResponse:
        """Return all known jobs."""
        jobs = [self._codec.to_payload(item) for item in self._job_store.list_jobs()]
        return JSONResponse(content={"jobs": jobs})

    async def get_job(self, job_id: str) -> JSONResponse:
        """Return one job by id."""
        snapshot = self._job_store.get(job_id)
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        return JSONResponse(content=self._codec.to_payload(snapshot))

    async def resume_job(self, job_id: str) -> JSONResponse:
        """Mark a resumable job running and return its resume plan."""
        try:
            plan = self._resume_service.resume_job(job_id)
        except InvalidJobError as error:
            message = str(error)
            status_code = 404 if message == "job not found" else 409
            return JSONResponse(status_code=status_code, content={"error": message})
        return JSONResponse(content=self._resume_codec.to_payload(plan))

    def resolve_job(self, job_id: str) -> JSONResponse:
        """Resolve playlist metadata for a job and persist tracks once."""
        try:
            snapshot = self._resolve_service.resolve_job(job_id)
        except InvalidJobError as error:
            message = str(error)
            status_code = 404 if message == "job not found" else 400
            return JSONResponse(status_code=status_code, content={"error": message})
        return JSONResponse(content=self._codec.to_payload(snapshot))
