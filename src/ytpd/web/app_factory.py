from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.progress_calculator import ProgressCalculator
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
    ) -> None:
        self._templates_dir = templates_dir
        self._static_dir = static_dir
        self._config = config
        self._config_store = config_store
        self._job_store = job_store
        self._progress_calculator = progress_calculator

    def build(self) -> FastAPI:
        """Create the app with templates, static assets, pages, and APIs."""
        templates = Jinja2Templates(directory=str(self._templates_dir))
        index_handler = IndexHandler(templates, self._config)
        config_handler = ConfigApiHandler(self._config_store)
        jobs_handler = JobsApiHandler(self._job_store)
        progress_handler = ProgressApiHandler(
            self._job_store,
            self._progress_calculator,
            ProgressSnapshotCodec(),
        )
        app = FastAPI(title="YTPlaylistDownloader")
        app.mount("/static", StaticFiles(directory=str(self._static_dir)), name="static")
        app.add_api_route("/", index_handler.handle, methods=["GET"])
        app.add_api_route("/api/config", config_handler.get_config, methods=["GET"])
        app.add_api_route("/api/config", config_handler.put_config, methods=["PUT"])
        app.add_api_route("/api/jobs", jobs_handler.create_job, methods=["POST"])
        app.add_api_route("/api/jobs", jobs_handler.list_jobs, methods=["GET"])
        app.add_api_route("/api/jobs/{job_id}", jobs_handler.get_job, methods=["GET"])
        app.add_api_route(
            "/api/jobs/{job_id}/progress",
            progress_handler.get_progress,
            methods=["GET"],
        )
        return app
