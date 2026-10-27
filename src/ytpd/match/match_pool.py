from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait

from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.ports.youtube_matcher import YoutubeMatcher


class MatchPool:
    """Match many tracks in parallel using an injected YouTube matcher."""

    def __init__(
        self,
        matcher: YoutubeMatcher,
        max_workers: int,
        cancel_flag: JobCancelFlag,
    ) -> None:
        self._matcher = matcher
        self._max_workers = max(1, max_workers)
        self._cancel_flag = cancel_flag

    def run(self, tracks: list[TrackRef]) -> list[MatchResult]:
        """Match every pending track and return results in pending-input order."""
        pending = [track for track in tracks if track.needs_youtube_match()]
        if len(pending) == 0:
            return []
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            return list(pool.map(self._matcher.match, pending))

    def iter_results(self, tracks: list[TrackRef]) -> Iterator[MatchResult]:
        """Yield match results as they finish; stop queueing when cancelled."""
        pending = [track for track in tracks if track.needs_youtube_match()]
        if len(pending) == 0:
            return
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            yield from self._drain(pool, pending)

    def _drain(
        self,
        pool: ThreadPoolExecutor,
        pending: list[TrackRef],
    ) -> Iterator[MatchResult]:
        queue = list(pending)
        in_flight: dict[Future[MatchResult], TrackRef] = {}
        while queue or in_flight:
            while queue and len(in_flight) < self._max_workers:
                if self._cancel_flag.is_cancelled():
                    queue.clear()
                    break
                track = queue.pop(0)
                future = pool.submit(self._matcher.match, track)
                in_flight[future] = track
            if len(in_flight) == 0:
                break
            done, _ = wait(list(in_flight.keys()), return_when=FIRST_COMPLETED)
            for future in done:
                in_flight.pop(future, None)
                yield future.result()
