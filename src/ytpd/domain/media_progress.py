from dataclasses import dataclass, field

from ytpd.domain.persisted_match_candidate import PersistedMatchCandidate
from ytpd.domain.track_phase import TrackPhase


@dataclass(frozen=True)
class MediaProgress:
    """Progress for one media currently in an active pipeline phase."""

    track_id: str
    title: str
    artist: str
    phase: TrackPhase
    detail: str
    candidates: list[PersistedMatchCandidate] = field(default_factory=list)
