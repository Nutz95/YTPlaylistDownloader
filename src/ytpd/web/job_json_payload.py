from typing import NotRequired, TypedDict

from ytpd.web.job_status_name import JobStatusName
from ytpd.web.pipeline_stage_name import PipelineStageName
from ytpd.web.source_kind_name import SourceKindName
from ytpd.web.track_json_payload import TrackJsonPayload


class JobJsonPayload(TypedDict):
    """JSON shape for one job in job API responses."""

    job_id: str
    source_url: str
    source_kind: SourceKindName
    status: JobStatusName
    error_message: str | None
    tracks: list[TrackJsonPayload]
    pipeline_stage: NotRequired[PipelineStageName | None]
    source_title: NotRequired[str | None]
