from typing import TypedDict


class MediaProgressJsonPayload(TypedDict):
    """JSON shape for one active media progress row."""

    track_id: str
    title: str
    phase_label: str
    detail: str
