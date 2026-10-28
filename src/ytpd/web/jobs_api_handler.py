from collections.abc import Mapping

from fastapi import Request
from fastapi.responses import JSONResponse

from ytpd.jobs.duplicate_source_url_error import DuplicateSourceUrlError
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_delete_service import JobDeleteService
from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_not_found_error import JobNotFoundError
from ytpd.jobs.job_pipeline_runner import JobPipelineRunner
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_resume_plan_codec import JobResumePlanCodec
from ytpd.jobs.job_resume_service import JobResumeService
from ytpd.jobs.job_retry_failed_service import JobRetryFailedService
from ytpd.jobs.job_snapshot_codec import JobSnapshotCodec
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_track_youtube_override_service import (
    JobTrackYoutubeOverrideService,
)
from ytpd.jobs.job_transcode_service import JobTranscodeService
from ytpd.jobs.pipeline_busy_error import PipelineBusyError
from ytpd.web.job_list_item_codec import JobListItemCodec


class JobsApiHandler:
    """HTTP handlers for job create/resolve/match/download/transcode/resume."""

    def __init__(
        self,
        job_store: JobStore,
        resume_service: JobResumeService,
        resolve_service: JobResolveService,
        match_service: JobMatchService,
        download_service: JobDownloadService,
        transcode_service: JobTranscodeService,
        pipeline_runner: JobPipelineRunner,
        retry_failed_service: JobRetryFailedService,
        youtube_override_service: JobTrackYoutubeOverrideService,
        delete_service: JobDeleteService,
    ) -> None:
        self._job_store = job_store
        self._resume_service = resume_service
        self._resolve_service = resolve_service
        self._match_service = match_service
        self._download_service = download_service
        self._transcode_service = transcode_service
        self._pipeline_runner = pipeline_runner
        self._retry_failed_service = retry_failed_service
        self._youtube_override_service = youtube_override_service
        self._delete_service = delete_service
        self._codec = JobSnapshotCodec()
        self._list_codec = JobListItemCodec()
        self._resume_codec = JobResumePlanCodec()

    async def create_job(self, request: Request) -> JSONResponse:
        """Create a queued job and drain the FIFO so it starts when the runner is free."""
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
        except DuplicateSourceUrlError as error:
            return JSONResponse(status_code=409, content={"error": str(error)})
        except InvalidJobError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})
        started = self._pipeline_runner.drain_queue()
        ours_started = started is not None and started.job_id == snapshot.job_id
        payload = dict(
            self._codec.to_payload(started if ours_started else snapshot)
        )
        payload["started"] = ours_started
        return JSONResponse(status_code=201, content=payload)

    async def list_jobs(self) -> JSONResponse:
        """Return lightweight job summaries (no track bodies)."""
        jobs = [
            self._list_codec.to_payload(item) for item in self._job_store.list_jobs()
        ]
        return JSONResponse(content={"jobs": jobs})

    async def get_job(self, job_id: str) -> JSONResponse:
        """Return one job by id."""
        snapshot = self._job_store.get(job_id)
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        return JSONResponse(content=self._codec.to_payload(snapshot))

    async def resume_job(self, job_id: str) -> JSONResponse:
        """Validate a resume plan, then start the pipeline in the background."""
        try:
            plan = self._resume_service.resume_job(job_id)
        except InvalidJobError as error:
            message = str(error)
            status_code = 404 if message == "job not found" else 409
            return JSONResponse(status_code=status_code, content={"error": message})
        body = dict(self._resume_codec.to_payload(plan))
        try:
            self._pipeline_runner.start(job_id)
        except PipelineBusyError as error:
            body["started"] = False
            return JSONResponse(status_code=409, content={**body, "error": str(error)})
        except JobNotFoundError as error:
            return JSONResponse(status_code=404, content={"error": str(error)})
        except InvalidJobError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})
        body["started"] = True
        return JSONResponse(content=body)

    def resolve_job(self, job_id: str) -> JSONResponse:
        """Resolve playlist metadata for a job and persist tracks once."""
        try:
            snapshot = self._resolve_service.resolve_job(job_id)
        except InvalidJobError as error:
            status_code = 404 if "not found" in str(error) else 400
            return JSONResponse(status_code=status_code, content={"error": str(error)})
        return JSONResponse(content=self._codec.to_payload(snapshot))

    def match_job(self, job_id: str) -> JSONResponse:
        """Match unresolved tracks for a job and persist YouTube URLs."""
        try:
            snapshot = self._match_service.match_job(job_id)
        except InvalidJobError as error:
            status_code = 404 if "not found" in str(error) else 400
            return JSONResponse(status_code=status_code, content={"error": str(error)})
        return JSONResponse(content=self._codec.to_payload(snapshot))

    def download_job(self, job_id: str) -> JSONResponse:
        """Download matched tracks for a job and persist download phases."""
        try:
            snapshot = self._download_service.download_job(job_id)
        except InvalidJobError as error:
            status_code = 404 if "not found" in str(error) else 400
            return JSONResponse(status_code=status_code, content={"error": str(error)})
        return JSONResponse(content=self._codec.to_payload(snapshot))

    def transcode_job(self, job_id: str) -> JSONResponse:
        """Transcode downloaded tracks for a job into destination MP3 files."""
        try:
            snapshot = self._transcode_service.transcode_job(job_id)
        except InvalidJobError as error:
            status_code = 404 if "not found" in str(error) else 400
            return JSONResponse(status_code=status_code, content={"error": str(error)})
        return JSONResponse(content=self._codec.to_payload(snapshot))

    def run_job(self, job_id: str) -> JSONResponse:
        """Start the full pipeline in the background and return immediately."""
        try:
            snapshot = self._pipeline_runner.start(job_id)
        except PipelineBusyError as error:
            return JSONResponse(status_code=409, content={"error": str(error)})
        except JobNotFoundError as error:
            return JSONResponse(status_code=404, content={"error": str(error)})
        except InvalidJobError as error:
            return JSONResponse(status_code=400, content={"error": str(error)})
        body = dict(self._codec.to_payload(snapshot))
        body["started"] = True
        return JSONResponse(content=body)

    def cancel_job(self, job_id: str) -> JSONResponse:
        """Cancel the pipeline and persist CANCELLED status immediately."""
        snapshot = self._job_store.get(job_id)
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        cancelled = self._pipeline_runner.cancel(job_id)
        if cancelled is None:
            return JSONResponse(status_code=404, content={"error": "job not found"})
        body = dict(self._codec.to_payload(cancelled))
        body["ok"] = True
        return JSONResponse(content=body)

    def delete_job(self, job_id: str) -> JSONResponse:
        """Delete a non-running job and its work directory."""
        try:
            self._delete_service.delete(job_id)
        except InvalidJobError as error:
            status_code = 404 if "not found" in str(error) else 409
            return JSONResponse(status_code=status_code, content={"error": str(error)})
        return JSONResponse(content={"ok": True, "job_id": job_id})

    def delete_completed_jobs(self) -> JSONResponse:
        """Delete every completed job checkpoint (output MP3s are kept)."""
        deleted_job_ids = self._delete_service.delete_completed()
        return JSONResponse(
            content={
                "ok": True,
                "deleted_count": len(deleted_job_ids),
                "deleted_job_ids": deleted_job_ids,
            }
        )

    def retry_failed_job(self, job_id: str) -> JSONResponse:
        """Reset failed tracks and start the pipeline again for those tracks."""
        try:
            prepared = self._retry_failed_service.retry_failed(job_id)
            started = self._pipeline_runner.start(prepared.job_id)
        except PipelineBusyError as error:
            return JSONResponse(status_code=409, content={"error": str(error)})
        except JobNotFoundError as error:
            return JSONResponse(status_code=404, content={"error": str(error)})
        except InvalidJobError as error:
            return JSONResponse(status_code=409, content={"error": str(error)})
        body = dict(self._codec.to_payload(started))
        body["started"] = True
        body["retried"] = True
        return JSONResponse(content=body)

    async def override_track_youtube(
        self,
        job_id: str,
        track_id: str,
        request: Request,
    ) -> JSONResponse:
        """Force a YouTube URL on a failed track and restart the pipeline."""
        body = await request.json()
        if not isinstance(body, Mapping):
            return JSONResponse(
                status_code=400,
                content={"error": "JSON body must be an object"},
            )
        raw_url = body.get("youtube_url")
        if not isinstance(raw_url, str):
            return JSONResponse(
                status_code=400,
                content={"error": "youtube_url must be a non-empty string"},
            )
        try:
            prepared = self._youtube_override_service.apply(job_id, track_id, raw_url)
            started = self._pipeline_runner.start(prepared.job_id)
        except PipelineBusyError as error:
            return JSONResponse(status_code=409, content={"error": str(error)})
        except JobNotFoundError as error:
            return JSONResponse(status_code=404, content={"error": str(error)})
        except InvalidJobError as error:
            status_code = 404 if "not found" in str(error) else 400
            return JSONResponse(status_code=status_code, content={"error": str(error)})
        payload = dict(self._codec.to_payload(started))
        payload["started"] = True
        payload["overridden"] = True
        return JSONResponse(content=payload)
