from concurrent.futures import ThreadPoolExecutor

from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef
from ytpd.ports.youtube_matcher import YoutubeMatcher


class MatchPool:
    """Match many tracks in parallel using an injected YouTube matcher."""

    def __init__(self, matcher: YoutubeMatcher, max_workers: int) -> None:
        self._matcher = matcher
        self._max_workers = max(1, max_workers)

    def run(self, tracks: list[TrackRef]) -> list[MatchResult]:
        """Match every pending track and return one result per pending track."""
        pending = [track for track in tracks if track.needs_youtube_match()]
        if len(pending) == 0:
            return []
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            return list(pool.map(self._matcher.match, pending))
