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

    def needs_youtube_match(self) -> bool:
        """True when the track still needs a YouTube URL (not terminal)."""
        if self.phase is TrackPhase.SKIPPED or self.phase is TrackPhase.DONE:
            return False
        return self.youtube_url is None or self.youtube_url.strip() == ""
