from dataclasses import dataclass

from ytpd.domain.deezer_track_entry import DeezerTrackEntry


@dataclass(frozen=True)
class DeezerTracksPage:
    """One page of Deezer playlist tracks plus an optional next URL."""

    tracks: list[DeezerTrackEntry]
    next_url: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tracks", list(self.tracks))
