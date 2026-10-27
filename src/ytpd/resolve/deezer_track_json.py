from typing import NotRequired, TypedDict

from ytpd.resolve.deezer_artist_json import DeezerArtistJson


class DeezerTrackJson(TypedDict):
    """Subset of a Deezer track object used when parsing playlist pages."""

    id: int | str
    title: str
    artist: NotRequired[DeezerArtistJson]
    duration: NotRequired[int | float]
