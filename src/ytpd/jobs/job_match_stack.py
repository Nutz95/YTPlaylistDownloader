from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_store import JobStore
from ytpd.match.match_pool import MatchPool
from ytpd.match.static_match_scorer import StaticMatchScorer
from ytpd.match.static_youtube_matcher import StaticYoutubeMatcher
from ytpd.ports.youtube_search_client import YoutubeSearchClient


class JobMatchStack:
    """Wire search client + static matcher into a job match service."""

    def __init__(
        self,
        job_store: JobStore,
        search_client: YoutubeSearchClient,
        max_workers: int,
    ) -> None:
        matcher = StaticYoutubeMatcher(search_client, StaticMatchScorer())
        self.match_service = JobMatchService(
            job_store,
            MatchPool(matcher, max_workers=max_workers),
        )
