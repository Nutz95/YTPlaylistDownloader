from dataclasses import dataclass, field

from ytpd.domain.match_candidate import MatchCandidate


@dataclass(frozen=True)
class MatchResult:
    """Outcome of matching one track to a YouTube URL."""

    track_id: str
    matched: bool
    candidate: MatchCandidate | None
    error_message: str | None
    candidates: list[MatchCandidate] = field(default_factory=list)
