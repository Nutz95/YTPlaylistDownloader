from dataclasses import dataclass


@dataclass(frozen=True)
class DeezerTrackEntry:
    """One Deezer playlist track after API resolve."""

    deezer_id: str
    title: str
    artist: str
    duration_sec: int | None
