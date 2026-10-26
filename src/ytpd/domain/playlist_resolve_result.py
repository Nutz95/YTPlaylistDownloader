from dataclasses import dataclass

from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_ref import TrackRef


@dataclass(frozen=True)
class PlaylistResolveResult:
    """Resolved playlist or single-video metadata ready for checkpointing."""

    source_kind: SourceKind
    tracks: list[TrackRef]

    def __post_init__(self) -> None:
        object.__setattr__(self, "tracks", list(self.tracks))
