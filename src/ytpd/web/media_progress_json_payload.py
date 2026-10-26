from typing import TypedDict

from ytpd.web.track_phase_name import TrackPhaseName


class MediaProgressJsonPayload(TypedDict):
    """JSON shape for one active media progress row."""

    track_id: str
    title: str
    phase_label: TrackPhaseName
    detail: str
