from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_store import JobStore
from ytpd.match.match_pool import MatchPool
from ytpd.ports.youtube_matcher import YoutubeMatcher


class JobMatchStack:
    """Wire an injected matcher into a job match service."""

    def __init__(
        self,
        job_store: JobStore,
        matcher: YoutubeMatcher,
        max_workers: int,
    ) -> None:
        self.match_service = JobMatchService(
            job_store,
            MatchPool(matcher, max_workers=max_workers),
        )
