from dataclasses import dataclass

from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_ref import TrackRef


@dataclass(frozen=True)
class PlaylistResolveResult:
    """Typed result of resolving a playlist URL into tracks."""

    source_kind: SourceKind
    tracks: list[TrackRef]
