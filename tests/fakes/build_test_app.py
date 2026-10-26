from pathlib import Path

from fastapi import FastAPI

from tests.fakes.fake_deezer_api_client import FakeDeezerApiClient
from tests.fakes.fake_lm_studio_http_transport import FakeLmStudioHttpTransport
from tests.fakes.fake_youtube_search_client import FakeYoutubeSearchClient
from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
from ytpd.config.app_config import AppConfig
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_resume_stack import JobResumeStack
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
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
        )
        lm_settings = LmStudioSettings(
            base_url=config.lm_base_url,
            model=config.lm_model,
            timeout_sec=config.lm_timeout_sec,
        )
        resolved_search = search_client or FakeYoutubeSearchClient({})
        transport = lm_transport or FakeLmStudioHttpTransport(
            ["test-model"], [], offline=True
        )
        matcher = CascadingYoutubeMatcher(
            YoutubeCandidateFetcher(resolved_search, StaticMatchScorer()),
            StaticMatchDecider(),
            HttpLmStudioClient(transport, lm_settings),
            GpuResourceGate(),
        )
        match_stack = JobMatchStack(
            resume_stack.job_store,
            matcher,
            max_workers=2,
        )
        return AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            store,
            resume_stack.job_store,
            ProgressCalculator(),
            resume_stack.resume_service,
            resolve_stack.resolve_service,
            match_stack.match_service,
        ).build()
