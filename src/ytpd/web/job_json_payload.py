from typing import TypedDict

from ytpd.web.track_json_payload import TrackJsonPayload


class JobJsonPayload(TypedDict):
    """JSON shape for one job in job API responses."""

    job_id: str
    source_url: str
    source_kind: str
    status: str
    error_message: str | None
    tracks: list[TrackJsonPayload]
