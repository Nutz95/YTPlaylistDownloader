from pathlib import Path

from ytpd.config.app_config import AppConfig
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.lmstudio.http_lm_studio_client import HttpLmStudioClient
from ytpd.lmstudio.httpx_lm_studio_http_transport import HttpxLmStudioHttpTransport
from ytpd.lmstudio.lm_studio_runtime_coordinator import LmStudioRuntimeCoordinator
from ytpd.lmstudio.lm_studio_settings import LmStudioSettings
from ytpd.match.cascading_youtube_matcher import CascadingYoutubeMatcher
from ytpd.match.static_match_decider import StaticMatchDecider
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.youtube_candidate_fetcher import YoutubeCandidateFetcher
from ytpd.ports.youtube_search_client import YoutubeSearchClient
from ytpd.runtime.gpu_resource_gate import GpuResourceGate

_LM_MATCH_CONTEXT_LENGTH = 8192


class MatchStackFactory:
    """Build a cascading match stack from config and a search client."""

    def build(
        self,
        job_store: JobStore,
        config: AppConfig,
        search_client: YoutubeSearchClient,
        max_workers: int,
        resource_gate: GpuResourceGate,
        cancel_flag: JobCancelFlag,
        work_dir: Path,
        dest_dir: Path,
    ) -> JobMatchStack:
        """Wire LM Studio + static cascade into ``JobMatchStack``."""
        lm_settings = LmStudioSettings(
            base_url=config.lm_base_url,
            model=config.lm_model,
            timeout_sec=config.lm_timeout_sec,
            context_length=_LM_MATCH_CONTEXT_LENGTH,
        )
        transport = HttpxLmStudioHttpTransport(lm_settings)
        model_runtime = LmStudioRuntimeCoordinator(lm_settings)
        matcher = CascadingYoutubeMatcher(
            YoutubeCandidateFetcher(search_client, StaticMatchScorer()),
            StaticMatchDecider(),
            HttpLmStudioClient(transport, lm_settings, model_runtime),
            resource_gate,
        )
        return JobMatchStack(
            job_store,
            matcher,
            max_workers=max_workers,
            cancel_flag=cancel_flag,
            request_aborter=transport,
            paths=TrackArtifactPaths(work_dir, dest_dir),
            model_runtime=model_runtime,
        )
