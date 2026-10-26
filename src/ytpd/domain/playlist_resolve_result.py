from dataclasses import dataclass

from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_ref import TrackRef


@dataclass(frozen=True)
class PlaylistResolveResult:
    """Resolved playlist or single-video metadata ready for checkpointing."""

    source_kind: SourceKind
    tracks: tuple[TrackRef, ...]
