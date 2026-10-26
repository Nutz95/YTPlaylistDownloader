from dataclasses import dataclass

from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_transcode_service import JobTranscodeService
from ytpd.ports.output_catalog import OutputCatalog


@dataclass(frozen=True)
class ComposedJobStacks:
    """Resolve, match, download, and transcode services from the composition root."""

    resolve_service: JobResolveService
    match_service: JobMatchService
    download_service: JobDownloadService
    transcode_service: JobTranscodeService
    catalog: OutputCatalog
