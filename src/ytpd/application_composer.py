import os
from pathlib import Path

from ytpd.composed_application import ComposedApplication
from ytpd.composed_job_stacks import ComposedJobStacks
from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.config.writable_config_path import WritableConfigPath
from ytpd.download.download_resume_policy import DownloadResumePolicy
from ytpd.download.ytdlp_downloader import YtdlpDownloader
from ytpd.jobs.job_download_stack import JobDownloadStack
from ytpd.jobs.job_orchestrator_stack import JobOrchestratorStack
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_resume_stack import JobResumeStack
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.match.match_stack_factory import MatchStackFactory
from ytpd.resolve.deezer_playlist_api_client import DeezerPlaylistApiClient
from ytpd.resolve.httpx_deezer_http_transport import HttpxDeezerHttpTransport
from ytpd.resolve.subprocess_youtube_search_client import SubprocessYoutubeSearchClient
from ytpd.resolve.subprocess_ytdlp_flat_playlist_client import (
    SubprocessYtdlpFlatPlaylistClient,
)
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser
from ytpd.runtime.gpu_resource_gate import GpuResourceGate
from ytpd.runtime.python_version_guard import PythonVersionGuard
from ytpd.runtime.sys_interpreter_version_provider import SysInterpreterVersionProvider
from ytpd.transcode.transcode_stack_factory import TranscodeStackFactory
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


class ApplicationComposer:
    """Composition root that wires runtime checks, settings, and the web app."""

    def compose(self) -> ComposedApplication:
        """Build a ready-to-serve application with config, jobs, and GIL warning."""
        gil_warning = PythonVersionGuard().check(
            SysInterpreterVersionProvider().read()
        )
        path_validator = PathValidator()
        config_store = AppConfigStore(
            WritableConfigPath().resolve(),
            path_validator,
        )
        config = config_store.load()
        work_dir = path_validator.ensure_directory(config.work_dir)
        dest_dir = path_validator.ensure_directory(config.dest_dir)
        resume_stack = JobResumeStack(
            SqliteJobCheckpointStore(work_dir / "jobs.db"),
            work_dir,
            dest_dir,
        )
        resume_stack.resume_service.mark_stale_running_interrupted()
        resource_gate = GpuResourceGate()
        stacks = self._build_job_stacks(
            resume_stack.job_store, config, work_dir, dest_dir, resource_gate
        )
        app = AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            config_store,
            resume_stack.job_store,
            ProgressCalculator(),
            resume_stack.resume_service,
            stacks.resolve_service,
            stacks.match_service,
            stacks.download_service,
            stacks.transcode_service,
            stacks.catalog,
            stacks.orchestrator,
        ).build()
        return ComposedApplication(
            app=app,
            settings=config,
            gil_warning=gil_warning,
        )

    def _build_job_stacks(
        self,
        job_store: JobStore,
        config: AppConfig,
        work_dir: Path,
        dest_dir: Path,
        resource_gate: GpuResourceGate,
    ) -> ComposedJobStacks:
        parser = YtdlpFlatPlaylistParser()
        resolve_stack = JobResolveStack(
            job_store,
            SubprocessYtdlpFlatPlaylistClient(parser),
            DeezerPlaylistApiClient(HttpxDeezerHttpTransport()),
        )
        pool_workers = min(8, os.cpu_count() or 4)
        match_stack = MatchStackFactory().build(
            job_store,
            config,
            SubprocessYoutubeSearchClient(parser),
            pool_workers,
            resource_gate,
        )
        paths = TrackArtifactPaths(work_dir, dest_dir)
        download_stack = JobDownloadStack(
            job_store,
            work_dir,
            dest_dir,
            YtdlpDownloader(paths, DownloadResumePolicy()),
            max_workers=pool_workers,
        )
        transcode_stack = TranscodeStackFactory().build(
            job_store, work_dir, dest_dir, resource_gate
        )
        orchestrator_stack = JobOrchestratorStack(
            job_store,
            work_dir,
            dest_dir,
            resolve_stack.resolve_service,
            match_stack.match_service,
            download_stack.download_service,
            transcode_stack.transcode_service,
            transcode_stack.catalog,
        )
        return ComposedJobStacks(
            resolve_service=resolve_stack.resolve_service,
            match_service=match_stack.match_service,
            download_service=download_stack.download_service,
            transcode_service=transcode_stack.transcode_service,
            catalog=transcode_stack.catalog,
            orchestrator=orchestrator_stack.orchestrator,
        )
