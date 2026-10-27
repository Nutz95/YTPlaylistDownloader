from typing import TypedDict

from ytpd.web.media_progress_json_payload import MediaProgressJsonPayload


class ProgressSnapshotJsonPayload(TypedDict):
    """JSON shape for a job progress snapshot."""

    job_id: str
    percent: float
    completed_tracks: int
    total_tracks: int
    label: str
    stage: str
    stage_done: int
    stage_total: int
    active_media: list[MediaProgressJsonPayload]
    failed_media: list[MediaProgressJsonPayload]
