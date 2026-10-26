from typing import Protocol

from ytpd.domain.lm_studio_match_choice import LmStudioMatchChoice
from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.track_ref import TrackRef


class LmStudioClient(Protocol):
    """Ask LM Studio to pick the best YouTube candidate for a track."""

    def choose_match(
        self,
        track: TrackRef,
        candidates: list[MatchCandidate],
    ) -> LmStudioMatchChoice:
        """Return the chosen candidate index, or a failure choice."""
