from pathlib import Path

from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_cancel_finalizer import JobCancelFinalizer
from ytpd.jobs.job_download_stack import JobDownloadStack
from ytpd.jobs.job_download_transcode_coordinator import (
    JobDownloadTranscodeCoordinator,
)
from ytpd.jobs.job_match_stack import JobMatchStack
from ytpd.jobs.job_orchestrator import JobOrchestrator
from ytpd.jobs.job_pipeline_runner import JobPipelineRunner
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_stack import JobTranscodeStack
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.output_catalog import OutputCatalog


class JobOrchestratorStack:
    """Wire pipeline services into a single job orchestrator."""

    def __init__(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        resolve_service: JobResolveService,
        match_stack: JobMatchStack,
        download_stack: JobDownloadStack,
        transcode_stack: JobTranscodeStack,
        catalog: OutputCatalog,
        cancel_flag: JobCancelFlag,
    ) -> None:
        self.cancel_flag = cancel_flag
        paths = download_stack.paths
        probe = PathTrackArtifactProbe(paths)
        coordinator = JobDownloadTranscodeCoordinator(
            job_store,
            download_stack.download_pool,
            transcode_stack.scheduler,
            probe,
            TrackStateMachine(),
            paths,
            cancel_flag,
            download_stack.failure_log,
            download_stack.phase_healer,
            transcode_pool_workers=transcode_stack.scheduler.backend_count(),
        )
        self.orchestrator = JobOrchestrator(
            job_store,
            resolve_service,
            match_stack.match_service,
            coordinator,
            PathTrackArtifactProbe(paths),
            catalog,
            cancel_flag,
            match_stack.model_runtime,
        )
        self.pipeline_runner = JobPipelineRunner(
            job_store,
            self.orchestrator,
            match_stack.request_aborter,
            JobCancelFinalizer(job_store),
        )
