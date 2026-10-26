from typing import Protocol

from ytpd.domain.match_result import MatchResult
from ytpd.domain.track_ref import TrackRef


class YoutubeMatcher(Protocol):
    """Match one track to a YouTube URL."""

    def match(self, track: TrackRef) -> MatchResult:
        """Return a match result for ``track``."""
