from dataclasses import dataclass

from ytpd.domain.global_progress import GlobalProgress
from ytpd.domain.media_progress import MediaProgress


@dataclass(frozen=True)
class ProgressSnapshot:
    """UI-facing progress view for one job."""

    job_id: str
    global_progress: GlobalProgress
    active_media: list[MediaProgress]

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_media", list(self.active_media))
