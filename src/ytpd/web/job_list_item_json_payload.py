from typing import NotRequired, TypedDict

from ytpd.web.job_status_name import JobStatusName
from ytpd.web.pipeline_stage_name import PipelineStageName
from ytpd.web.source_kind_name import SourceKindName


class JobListItemJsonPayload(TypedDict):
    """JSON shape for one row in the jobs list API."""

    job_id: str
    source_url: str
    source_kind: SourceKindName
    status: JobStatusName
    track_count: int
    error_message: str | None
    pipeline_stage: NotRequired[PipelineStageName | None]
