from pathlib import Path

from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_orchestrator import JobOrchestrator
from ytpd.jobs.job_resolve_service import JobResolveService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_service import JobTranscodeService
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.output_catalog import OutputCatalog


class JobOrchestratorStack:
    """Wire pipeline services into a single job orchestrator."""

    def __init__(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        resolve_service: JobResolveService,
        match_service: JobMatchService,
        download_service: JobDownloadService,
        transcode_service: JobTranscodeService,
        catalog: OutputCatalog,
    ) -> None:
        self.cancel_flag = JobCancelFlag()
        self.orchestrator = JobOrchestrator(
            job_store,
            resolve_service,
            match_service,
            download_service,
            transcode_service,
            PathTrackArtifactProbe(TrackArtifactPaths(work_dir, dest_dir)),
            catalog,
            self.cancel_flag,
        )
