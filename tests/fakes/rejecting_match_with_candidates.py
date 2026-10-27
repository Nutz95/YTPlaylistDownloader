from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_result import MatchResult
from ytpd.domain.match_score import MatchScore
from ytpd.domain.track_ref import TrackRef


class RejectingMatchWithCandidates:
    """Matcher that always fails but returns scored candidates for UI persist."""

    def match(self, track: TrackRef) -> MatchResult:
        """Return MATCH_FAILED with one candidate."""
        return MatchResult(
            track_id=track.track_id,
            matched=False,
            candidate=None,
            error_message="no fit",
            candidates=[
                MatchCandidate(
                    "https://youtu.be/abc123",
                    "Cand Title",
                    "Cand Channel",
                    120,
                    MatchScore(40.0),
                )
            ],
        )
