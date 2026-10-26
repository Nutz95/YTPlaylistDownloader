from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.match_result import MatchResult

_MIN_SCORE = 55.0


class StaticMatchDecider:
    """Pick the best scored candidate above the static score floor."""

    def decide(self, track_id: str, candidates: list[MatchCandidate]) -> MatchResult:
        """Return a matched result when the best candidate clears the floor."""
        if len(candidates) == 0:
            return MatchResult(
                track_id=track_id,
                matched=False,
                candidate=None,
                error_message="no youtube search hits",
            )
        ranked = sorted(
            candidates,
            key=lambda item: item.score.value,
            reverse=True,
        )
        best = ranked[0]
        if best.score.value < _MIN_SCORE:
            return MatchResult(
                track_id=track_id,
                matched=False,
                candidate=best,
                error_message="best candidate below score floor",
            )
        return MatchResult(
            track_id=track_id,
            matched=True,
            candidate=best,
            error_message=None,
        )
