from typing import TypedDict

from ytpd.web.media_progress_json_payload import MediaProgressJsonPayload


class ProgressSnapshotJsonPayload(TypedDict):
    """JSON shape for a job progress snapshot."""

    job_id: str
    percent: float
    completed_tracks: int
    total_tracks: int
    label: str
    active_media: list[MediaProgressJsonPayload]
