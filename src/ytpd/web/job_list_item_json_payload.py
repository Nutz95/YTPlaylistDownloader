from typing import TypedDict

from ytpd.web.job_status_name import JobStatusName
from ytpd.web.source_kind_name import SourceKindName


class JobListItemJsonPayload(TypedDict):
    """JSON shape for one job row in the jobs list (no track bodies)."""

    job_id: str
    source_url: str
    source_kind: SourceKindName
    status: JobStatusName
    track_count: int
    error_message: str | None
