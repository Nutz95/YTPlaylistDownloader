from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef


class FakeYoutubeMatcher:
    """Return preloaded match results keyed by track id."""

    def __init__(self, results_by_track_id: dict[str, MatchResult]) -> None:
        self._results_by_track_id = dict(results_by_track_id)
        self.calls: list[str] = []

    def match(self, track: TrackRef) -> MatchResult:
        """Return the configured result for ``track``."""
        self.calls.append(track.track_id)
        return self._results_by_track_id[track.track_id]
