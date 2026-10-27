from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.jobs.job_delete_service import JobDeleteService
from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_pipeline_runner import JobPipelineRunner
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_resume_service import JobResumeService
from ytpd.jobs.job_retry_failed_service import JobRetryFailedService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_track_youtube_override_service import (
    JobTrackYoutubeOverrideService,
)
from ytpd.jobs.job_transcode_service import JobTranscodeService
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime
from ytpd.ports.output_catalog import OutputCatalog
from ytpd.web.app_lifespan import AppLifespan
from ytpd.web.catalog_api_handler import CatalogApiHandler
from ytpd.web.config_api_handler import ConfigApiHandler
from ytpd.web.index_handler import IndexHandler
from ytpd.web.jobs_api_handler import JobsApiHandler
from ytpd.web.progress_api_handler import ProgressApiHandler
from ytpd.web.progress_snapshot_codec import ProgressSnapshotCodec


class AppFactory:
    """Build the FastAPI application and register HTTP routes."""

    def __init__(
        self,
        templates_dir: Path,
        static_dir: Path,
        config: AppConfig,
        config_store: AppConfigStore,
        job_store: JobStore,
        progress_calculator: ProgressCalculator,
        resume_service: JobResumeService,
        resolve_service: JobResolveService,
        match_service: JobMatchService,
        download_service: JobDownloadService,
        transcode_service: JobTranscodeService,
        catalog: OutputCatalog,
        pipeline_runner: JobPipelineRunner,
        retry_failed_service: JobRetryFailedService,
        youtube_override_service: JobTrackYoutubeOverrideService,
        delete_service: JobDeleteService,
        lm_runtime: LmStudioModelRuntime,
    ) -> None:
        self._templates_dir = templates_dir
        self._static_dir = static_dir
        self._config = config
        self._config_store = config_store
        self._job_store = job_store
        self._progress_calculator = progress_calculator
        self._resume_service = resume_service
        self._resolve_service = resolve_service
        self._match_service = match_service
        self._download_service = download_service
        self._transcode_service = transcode_service
        self._catalog = catalog
        self._pipeline_runner = pipeline_runner
        self._retry_failed_service = retry_failed_service
        self._youtube_override_service = youtube_override_service
        self._delete_service = delete_service
        self._lm_runtime = lm_runtime

    def build(self) -> FastAPI:
        """Create the app with templates, static assets, pages, and APIs."""
        templates = Jinja2Templates(directory=str(self._templates_dir))
        app = FastAPI(
            title="YTPlaylistDownloader",
            lifespan=AppLifespan(self._pipeline_runner, self._lm_runtime).handle,
        )
        app.mount("/static", StaticFiles(directory=str(self._static_dir)), name="static")
        self._register_routes(app, templates)
        return app

    def _register_routes(self, app: FastAPI, templates: Jinja2Templates) -> None:
        index_handler = IndexHandler(templates, self._config)
        config_handler = ConfigApiHandler(self._config_store)
        jobs_handler = self._jobs_handler()
        progress_handler = ProgressApiHandler(
            self._job_store,
            self._progress_calculator,
            ProgressSnapshotCodec(),
        )
        catalog_handler = CatalogApiHandler(self._catalog)
        app.add_api_route("/", index_handler.handle, methods=["GET"])
        app.add_api_route("/api/config", config_handler.get_config, methods=["GET"])
        app.add_api_route("/api/config", config_handler.put_config, methods=["PUT"])
        self._register_job_routes(app, jobs_handler)
        app.add_api_route(
            "/api/jobs/{job_id}/progress",
            progress_handler.get_progress,
            methods=["GET"],
        )
        app.add_api_route(
            "/api/catalog", catalog_handler.list_catalog, methods=["GET"]
        )

    def _jobs_handler(self) -> JobsApiHandler:
        return JobsApiHandler(
            self._job_store,
            self._resume_service,
            self._resolve_service,
            self._match_service,
            self._download_service,
            self._transcode_service,
            self._pipeline_runner,
            self._retry_failed_service,
            self._youtube_override_service,
            self._delete_service,
        )

    def _register_job_routes(self, app: FastAPI, jobs_handler: JobsApiHandler) -> None:
        app.add_api_route("/api/jobs", jobs_handler.create_job, methods=["POST"])
        app.add_api_route("/api/jobs", jobs_handler.list_jobs, methods=["GET"])
        app.add_api_route("/api/jobs/{job_id}", jobs_handler.get_job, methods=["GET"])
        app.add_api_route(
            "/api/jobs/{job_id}", jobs_handler.delete_job, methods=["DELETE"]
        )
        app.add_api_route(
            "/api/jobs/{job_id}/resume", jobs_handler.resume_job, methods=["POST"]
        )
        app.add_api_route(
            "/api/jobs/{job_id}/resolve", jobs_handler.resolve_job, methods=["POST"]
        )
        app.add_api_route(
            "/api/jobs/{job_id}/match", jobs_handler.match_job, methods=["POST"]
        )
        app.add_api_route(
            "/api/jobs/{job_id}/download", jobs_handler.download_job, methods=["POST"]
        )
        app.add_api_route(
            "/api/jobs/{job_id}/transcode",
            jobs_handler.transcode_job,
            methods=["POST"],
        )
        app.add_api_route(
            "/api/jobs/{job_id}/run",
            jobs_handler.run_job,
            methods=["POST"],
        )
        app.add_api_route(
            "/api/jobs/{job_id}/cancel",
            jobs_handler.cancel_job,
            methods=["POST"],
        )
        app.add_api_route(
            "/api/jobs/{job_id}/retry-failed",
            jobs_handler.retry_failed_job,
            methods=["POST"],
        )
        app.add_api_route(
            "/api/jobs/{job_id}/tracks/{track_id}/youtube-override",
            jobs_handler.override_track_youtube,
            methods=["POST"],
        )
