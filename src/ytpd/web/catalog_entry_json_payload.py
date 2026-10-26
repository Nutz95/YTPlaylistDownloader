from typing import TypedDict


class CatalogEntryJsonPayload(TypedDict):
    """JSON shape for one catalogue entry."""

    track_id: str
    title: str
    artist: str
    mp3_path: str
    youtube_url: str | None
    deezer_id: str | None
