from pathlib import Path

from fastapi import FastAPI

from tests.fakes.fake_deezer_api_client import FakeDeezerApiClient
from tests.fakes.fake_lm_studio_http_transport import FakeLmStudioHttpTransport
from tests.fakes.fake_lm_studio_model_runtime import FakeLmStudioModelRuntime
from tests.fakes.fake_media_downloader import FakeMediaDownloader
from tests.fakes.fake_transcode_backend import FakeTranscodeBackend
from tests.fakes.fake_youtube_search_client import FakeYoutubeSearchClient
from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
from tests.fakes.fake_ytdlp_video_metadata_client import FakeYtdlpVideoMetadataClient
from ytpd.catalog.memory_output_catalog import MemoryOutputCatalog
from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_delete_service import JobDeleteService
from ytpd.jobs.job_download_stack import JobDownloadStack
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_orchestrator_stack import JobOrchestratorStack
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_resume_stack import JobResumeStack
from ytpd.jobs.job_retry_failed_service import JobRetryFailedService
from ytpd.jobs.job_track_youtube_override_service import (
    JobTrackYoutubeOverrideService,
)
from ytpd.jobs.job_transcode_stack import JobTranscodeStack
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.download.memory_download_progress_store import MemoryDownloadProgressStore
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.match.cascading_youtube_matcher import CascadingYoutubeMatcher
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from ytpd.ports.deezer_api_client import DeezerApiClient
from ytpd.ports.lm_studio_http_transport import LmStudioHttpTransport
from ytpd.ports.youtube_search_client import YoutubeSearchClient
from ytpd.ports.ytdlp_flat_playlist_client import YtdlpFlatPlaylistClient
from ytpd.runtime.gpu_resource_gate import GpuResourceGate
from ytpd.runtime.null_request_aborter import NullRequestAborter
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


class BuildTestApp:
    """Compose a FastAPI app for offline unit tests under ``tmp_path``."""

    def build(
        self,
        tmp_path: Path,
        ytdlp_client: YtdlpFlatPlaylistClient | None = None,
        deezer_client: DeezerApiClient | None = None,
        search_client: YoutubeSearchClient | None = None,
        lm_transport: LmStudioHttpTransport | None = None,
    ) -> FastAPI:
        """Create app + relative config dirs inside ``tmp_path`` (caller chdirs)."""
        store = AppConfigStore(tmp_path / "app.yaml", PathValidator())
        config = store.save(
            AppConfig(
                host="127.0.0.1",
                port=8765,
                work_dir=Path("work"),
                dest_dir=Path("out"),
                lm_base_url="http://127.0.0.1:1234/v1",
                lm_model="test-model",
                lm_timeout_sec=1.0,
                youtube_cookies_from_browser="",
                youtube_cookies_file="",
                ffmpeg_path="",
            )
        )
        resume_stack = JobResumeStack(
            SqliteJobCheckpointStore(tmp_path / "jobs.db"),
            tmp_path / "work",
            tmp_path / "out",
        )
        resolve_stack = JobResolveStack(
            resume_stack.job_store,
            ytdlp_client or FakeYtdlpFlatPlaylistClient({}),
            deezer_client or FakeDeezerApiClient({}),
            FakeYtdlpVideoMetadataClient({}),
        )
        lm_settings = LmStudioSettings(
            base_url=config.lm_base_url,
            model=config.lm_model,
            timeout_sec=config.lm_timeout_sec,
            context_length=8192,
        )
        resource_gate = GpuResourceGate()
        resolved_search = search_client or FakeYoutubeSearchClient({})
        transport = lm_transport or FakeLmStudioHttpTransport(
            ["test-model"], [], offline=True
        )
        lm_runtime = FakeLmStudioModelRuntime()
        matcher = CascadingYoutubeMatcher(
            YoutubeCandidateFetcher(resolved_search, StaticMatchScorer()),
            StaticMatchDecider(),
            HttpLmStudioClient(transport, lm_settings, lm_runtime),
            resource_gate,
        )
        cancel_flag = JobCancelFlag()
        aborter = NullRequestAborter()
        paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
        match_stack = JobMatchStack(
            resume_stack.job_store,
            matcher,
            max_workers=2,
            cancel_flag=cancel_flag,
            request_aborter=aborter,
            paths=paths,
            model_runtime=lm_runtime,
        )
        download_stack = JobDownloadStack(
            resume_stack.job_store,
            tmp_path / "work",
            tmp_path / "out",
            FakeMediaDownloader(paths, set()),
            max_workers=2,
            cancel_flag=cancel_flag,
        )
        catalog = MemoryOutputCatalog()
        transcode_stack = JobTranscodeStack(
            resume_stack.job_store,
            tmp_path / "work",
            tmp_path / "out",
            [
                FakeTranscodeBackend(TranscodeBackendKind.NVIDIA, paths),
                FakeTranscodeBackend(TranscodeBackendKind.CPU, paths),
            ],
            resource_gate,
            catalog=catalog,
        )
        orchestrator_stack = JobOrchestratorStack(
            resume_stack.job_store,
            tmp_path / "work",
            tmp_path / "out",
            resolve_stack.resolve_service,
            match_stack,
            download_stack,
            transcode_stack,
            catalog,
            cancel_flag,
        )
        retry_failed = JobRetryFailedService(
            resume_stack.job_store,
            PathTrackArtifactProbe(paths),
            paths,
        )
        return AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            store,
            resume_stack.job_store,
            ProgressCalculator(MemoryDownloadProgressStore()),
            resume_stack.resume_service,
            resolve_stack.resolve_service,
            match_stack.match_service,
            download_stack.download_service,
            transcode_stack.transcode_service,
            catalog,
            orchestrator_stack.pipeline_runner,
            retry_failed,
            JobTrackYoutubeOverrideService(resume_stack.job_store),
            JobDeleteService(
                resume_stack.job_store,
                orchestrator_stack.pipeline_runner,
                paths,
            ),
            lm_runtime,
        ).build()
