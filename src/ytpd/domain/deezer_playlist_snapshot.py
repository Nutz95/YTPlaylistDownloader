from dataclasses import dataclass

from ytpd.domain.deezer_track_entry import DeezerTrackEntry


@dataclass(frozen=True)
class DeezerPlaylistSnapshot:
    """Deezer playlist metadata plus its resolved tracks."""

    title: str | None
    tracks: list[DeezerTrackEntry]
