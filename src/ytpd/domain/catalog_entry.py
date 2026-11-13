from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEntry:
    """One finished destination file recorded in the output catalogue."""

    track_id: str
    title: str
    artist: str
    output_path: str
    youtube_url: str | None
    deezer_id: str | None
