from typing import TypedDict

from ytpd.web.source_kind_name import SourceKindName
from ytpd.web.track_phase_name import TrackPhaseName


class TrackJsonPayload(TypedDict):
    """JSON shape for one track in job API responses."""

    track_id: str
    title: str
    artist: str
    duration_sec: int | None
    source_kind: SourceKindName
    phase: TrackPhaseName
    youtube_url: str | None
    deezer_id: str | None
    error_message: str | None
