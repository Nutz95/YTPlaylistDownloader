import os

from ytpd.composed_application import ComposedApplication
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.config.writable_config_path import WritableConfigPath
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_resolve_stack import JobResolveStack
from ytpd.jobs.job_resume_stack import JobResumeStack
from ytpd.jobs.progress_calculator import ProgressCalculator
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.httpx_lm_studio_http_transport import HttpxLmStudioHttpTransport
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.match.cascading_youtube_matcher import CascadingYoutubeMatcher
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
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
        parser = YtdlpFlatPlaylistParser()
        resolve_stack = JobResolveStack(
            resume_stack.job_store,
            SubprocessYtdlpFlatPlaylistClient(parser),
            DeezerPlaylistApiClient(HttpxDeezerHttpTransport()),
        )
        lm_settings = LmStudioSettings(
            base_url=config.lm_base_url,
            model=config.lm_model,
            timeout_sec=config.lm_timeout_sec,
        )
        search_client = SubprocessYoutubeSearchClient(parser)
        scorer = StaticMatchScorer()
        fetcher = YoutubeCandidateFetcher(search_client, scorer)
        matcher = CascadingYoutubeMatcher(
            fetcher,
            StaticMatchDecider(),
            HttpLmStudioClient(HttpxLmStudioHttpTransport(lm_settings), lm_settings),
            GpuResourceGate(),
        )
        match_stack = JobMatchStack(
            resume_stack.job_store,
            matcher,
            max_workers=min(8, os.cpu_count() or 4),
        )
        app = AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            config_store,
            resume_stack.job_store,
            ProgressCalculator(),
            resume_stack.resume_service,
            resolve_stack.resolve_service,
            match_stack.match_service,
        ).build()
        return ComposedApplication(
            app=app,
            settings=config,
            gil_warning=gil_warning,
        )
