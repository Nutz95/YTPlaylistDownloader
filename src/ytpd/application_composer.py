from pathlib import Path

from ytpd.composed_application import ComposedApplication
from ytpd.composed_job_stacks import ComposedJobStacks
from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.config.writable_config_path import WritableConfigPath
from ytpd.download.download_resume_policy import DownloadResumePolicy
from ytpd.download.memory_download_progress_store import MemoryDownloadProgressStore
from ytpd.download.ytdlp_downloader import YtdlpDownloader
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_delete_service import JobDeleteService
from ytpd.jobs.job_download_stack import JobDownloadStack
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_orchestrator_stack import JobOrchestratorStack
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_resume_stack import JobResumeStack
from ytpd.jobs.job_retry_failed_service import JobRetryFailedService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_track_youtube_override_service import (
    JobTrackYoutubeOverrideService,
)
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
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
from ytpd.resolve.subprocess_ytdlp_video_metadata_client import (
    SubprocessYtdlpVideoMetadataClient,
)
from ytpd.resolve.ytdlp_argv_builder import YtdlpArgvBuilder
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser
from ytpd.resolve.ytdlp_video_metadata_parser import YtdlpVideoMetadataParser
from ytpd.runtime.gpu_resource_gate import GpuResourceGate
from ytpd.runtime.pool_worker_limits import PoolWorkerLimits
from ytpd.runtime.python_version_guard import PythonVersionGuard
from ytpd.runtime.sys_interpreter_version_provider import SysInterpreterVersionProvider
from ytpd.transcode.memory_transcode_progress_store import MemoryTranscodeProgressStore
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
        download_progress_store = MemoryDownloadProgressStore()
        transcode_progress_store = MemoryTranscodeProgressStore()
        stacks = self._build_job_stacks(
            resume_stack.job_store,
            config,
            work_dir,
            dest_dir,
            resource_gate,
            download_progress_store,
            transcode_progress_store,
        )
        paths = TrackArtifactPaths(work_dir, dest_dir)
        app = AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            config_store,
            resume_stack.job_store,
            ProgressCalculator(
                download_progress_store,
                transcode_progress_store,
                stacks.transcode_slot_count,
            ),
            resume_stack.resume_service,
            stacks.resolve_service,
            stacks.match_service,
            stacks.download_service,
            stacks.transcode_service,
            stacks.catalog,
            stacks.pipeline_runner,
            stacks.retry_failed_service,
            JobTrackYoutubeOverrideService(resume_stack.job_store),
            JobDeleteService(resume_stack.job_store, stacks.pipeline_runner, paths),
            stacks.lm_runtime,
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
        download_progress_store: MemoryDownloadProgressStore,
        transcode_progress_store: MemoryTranscodeProgressStore,
    ) -> ComposedJobStacks:
        """Wire resolve / match / download / transcode into composed stacks."""
        cancel_flag = JobCancelFlag()
        argv_builder = YtdlpArgvBuilder(
            config.youtube_cookies_from_browser,
            config.youtube_cookies_file,
        )
        paths = TrackArtifactPaths(work_dir, dest_dir)
        resolve_stack = self._build_resolve_stack(job_store, argv_builder)
        match_stack = self._build_match_stack(
            job_store, config, argv_builder, resource_gate, cancel_flag, work_dir, dest_dir
        )
        download_stack = self._build_download_stack(
            job_store, work_dir, dest_dir, paths, download_progress_store, argv_builder, cancel_flag
        )
        transcode_stack = TranscodeStackFactory().build(
            job_store,
            work_dir,
            dest_dir,
            resource_gate,
            config.ffmpeg_path,
            transcode_progress_store,
        )
        orchestrator_stack = JobOrchestratorStack(
            job_store,
            work_dir,
            dest_dir,
            resolve_stack.resolve_service,
            match_stack,
            download_stack,
            transcode_stack,
            transcode_stack.catalog,
            cancel_flag,
        )
        return ComposedJobStacks(
            resolve_service=resolve_stack.resolve_service,
            match_service=match_stack.match_service,
            download_service=download_stack.download_service,
            transcode_service=transcode_stack.transcode_service,
            catalog=transcode_stack.catalog,
            orchestrator=orchestrator_stack.orchestrator,
            pipeline_runner=orchestrator_stack.pipeline_runner,
            retry_failed_service=JobRetryFailedService(
                job_store, PathTrackArtifactProbe(paths), paths
            ),
            lm_runtime=match_stack.model_runtime,
            transcode_slot_count=transcode_stack.scheduler.backend_count(),
        )

    def _build_resolve_stack(
        self,
        job_store: JobStore,
        argv_builder: YtdlpArgvBuilder,
    ) -> JobResolveStack:
        parser = YtdlpFlatPlaylistParser()
        return JobResolveStack(
            job_store,
            SubprocessYtdlpFlatPlaylistClient(parser, argv_builder),
            DeezerPlaylistApiClient(HttpxDeezerHttpTransport()),
            SubprocessYtdlpVideoMetadataClient(
                YtdlpVideoMetadataParser(),
                argv_builder,
            ),
        )

    def _build_match_stack(
        self,
        job_store: JobStore,
        config: AppConfig,
        argv_builder: YtdlpArgvBuilder,
        resource_gate: GpuResourceGate,
        cancel_flag: JobCancelFlag,
        work_dir: Path,
        dest_dir: Path,
    ) -> JobMatchStack:
        parser = YtdlpFlatPlaylistParser()
        return MatchStackFactory().build(
            job_store,
            config,
            SubprocessYoutubeSearchClient(parser, argv_builder),
            PoolWorkerLimits().match_workers(),
            resource_gate,
            cancel_flag,
            work_dir,
            dest_dir,
        )

    def _build_download_stack(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        paths: TrackArtifactPaths,
        download_progress_store: MemoryDownloadProgressStore,
        argv_builder: YtdlpArgvBuilder,
        cancel_flag: JobCancelFlag,
    ) -> JobDownloadStack:
        return JobDownloadStack(
            job_store,
            work_dir,
            dest_dir,
            YtdlpDownloader(
                paths,
                DownloadResumePolicy(),
                download_progress_store,
                argv_builder=argv_builder,
            ),
            max_workers=PoolWorkerLimits().download_workers(),
            cancel_flag=cancel_flag,
        )
