from typing import TypedDict


class TrackJsonPayload(TypedDict):
    """JSON shape for one track in job API responses."""

    track_id: str
    title: str
    artist: str
    duration_sec: int | None
    source_kind: str
    phase: str
    youtube_url: str | None
    deezer_id: str | None
    error_message: str | None
