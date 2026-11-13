from dataclasses import dataclass

from ytpd.domain.job_media_mode import JobMediaMode


@dataclass(frozen=True)
class JobCreateRequest:
    """Validated fields for creating one job."""

    source_url: str
    media_mode: JobMediaMode
    force_reprocess: bool
