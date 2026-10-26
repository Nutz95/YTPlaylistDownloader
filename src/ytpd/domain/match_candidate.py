from dataclasses import dataclass

from ytpd.domain.match_score import MatchScore


@dataclass(frozen=True)
class MatchCandidate:
    """One YouTube search hit scored against a Deezer track."""

    youtube_url: str
    title: str
    channel: str
    duration_sec: int | None
    score: MatchScore
