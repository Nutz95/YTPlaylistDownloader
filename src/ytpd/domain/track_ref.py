from dataclasses import dataclass

from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase


@dataclass(frozen=True)
class TrackRef:
    """One playlist entry after resolve (and optional YouTube match)."""

    track_id: str
    title: str
    artist: str
    duration_sec: int | None
    source_kind: SourceKind
    phase: TrackPhase
    youtube_url: str | None
    deezer_id: str | None
    error_message: str | None
