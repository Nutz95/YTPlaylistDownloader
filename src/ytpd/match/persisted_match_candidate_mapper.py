from ytpd.domain.match_candidate import MatchCandidate
from ytpd.domain.persisted_match_candidate import PersistedMatchCandidate

_MAX_PERSISTED = 8


class PersistedMatchCandidateMapper:
    """Map scored search hits to persisted UI candidates (top N)."""

    def from_scored(self, candidates: list[MatchCandidate]) -> list[PersistedMatchCandidate]:
        """Return up to ``_MAX_PERSISTED`` candidates ordered by descending score."""
        ordered = sorted(candidates, key=lambda item: item.score.value, reverse=True)
        return [
            PersistedMatchCandidate(
                youtube_url=candidate.youtube_url,
                title=candidate.title,
                channel=candidate.channel,
                duration_sec=candidate.duration_sec,
            )
            for candidate in ordered[:_MAX_PERSISTED]
        ]
