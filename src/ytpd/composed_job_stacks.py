from dataclasses import dataclass

from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_resolve_service import JobResolveService


@dataclass(frozen=True)
class ComposedJobStacks:
    """Resolve, match, and download services wired by the composition root."""

    resolve_service: JobResolveService
    match_service: JobMatchService
    download_service: JobDownloadService
