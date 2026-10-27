from dataclasses import dataclass

from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_orchestrator import JobOrchestrator
from ytpd.jobs.job_pipeline_runner import JobPipelineRunner
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_retry_failed_service import JobRetryFailedService
from ytpd.jobs.job_transcode_service import JobTranscodeService
from ytpd.ports.lm_studio_model_runtime import LmStudioModelRuntime
from ytpd.ports.output_catalog import OutputCatalog


@dataclass(frozen=True)
class ComposedJobStacks:
    """Resolve through orchestrator services from the composition root."""

    resolve_service: JobResolveService
    match_service: JobMatchService
    download_service: JobDownloadService
    transcode_service: JobTranscodeService
    catalog: OutputCatalog
    orchestrator: JobOrchestrator
    pipeline_runner: JobPipelineRunner
    retry_failed_service: JobRetryFailedService
    lm_runtime: LmStudioModelRuntime
    transcode_slot_count: int
