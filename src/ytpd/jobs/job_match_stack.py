from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.match.match_pool import MatchPool
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime
from ytpd.ports.request_aborter import RequestAborter
from ytpd.ports.youtube_matcher import YoutubeMatcher


class JobMatchStack:
    """Wire an injected matcher into a job match service."""

    def __init__(
        self,
        job_store: JobStore,
        matcher: YoutubeMatcher,
        max_workers: int,
        cancel_flag: JobCancelFlag,
        request_aborter: RequestAborter,
        paths: TrackArtifactPaths,
        model_runtime: LmStudioModelRuntime,
    ) -> None:
        self.request_aborter = request_aborter
        self.model_runtime = model_runtime
        self.match_service = JobMatchService(
            job_store,
            MatchPool(matcher, max_workers=max_workers, cancel_flag=cancel_flag),
            cancel_flag,
            JobFailureLog(paths),
        )
