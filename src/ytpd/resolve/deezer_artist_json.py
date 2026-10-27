from typing import TypedDict


class DeezerArtistJson(TypedDict, total=False):
    """Subset of a Deezer artist object used when parsing tracks."""

    name: str
