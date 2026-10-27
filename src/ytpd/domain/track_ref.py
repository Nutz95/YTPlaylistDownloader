from dataclasses import dataclass, field

from ytpd.domain.persisted_match_candidate import PersistedMatchCandidate
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
    chapter_start_sec: float | None = None
    chapter_end_sec: float | None = None
    parent_video_id: str | None = None
    chapter_index: int | None = None
    match_candidates: list[PersistedMatchCandidate] = field(default_factory=list)

    def needs_youtube_match(self) -> bool:
        """True when the track still needs a YouTube URL (not terminal)."""
        if self.phase is TrackPhase.SKIPPED or self.phase is TrackPhase.DONE:
            return False
        return self.youtube_url is None or self.youtube_url.strip() == ""

    def has_chapter_slice(self) -> bool:
        """True when this track is a timed chapter segment of a parent video."""
        return (
            self.chapter_start_sec is not None
            and self.chapter_end_sec is not None
            and self.parent_video_id is not None
            and self.parent_video_id.strip() != ""
        )
