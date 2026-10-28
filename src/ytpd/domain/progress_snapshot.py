from dataclasses import dataclass

from ytpd.domain.global_progress import GlobalProgress
from ytpd.domain.job_status import JobStatus
from ytpd.domain.media_progress import MediaProgress


@dataclass(frozen=True)
class ProgressSnapshot:
    """UI-facing progress view for one job."""

    job_id: str
    job_status: JobStatus
    global_progress: GlobalProgress
    active_media: list[MediaProgress]
    failed_media: list[MediaProgress]
