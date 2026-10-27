from pathlib import Path

from ytpd.catalog.sqlite_output_catalog import SqliteOutputCatalog
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.job_transcode_service import JobTranscodeService
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.output_catalog import OutputCatalog
from ytpd.ports.resource_gate import ResourceGate
from ytpd.ports.transcode_backend import TranscodeBackend
from ytpd.transcode.transcode_scheduler import TranscodeScheduler


class JobTranscodeStack:
    """Wire backends + catalogue into a job transcode service."""

    def __init__(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        backends: list[TranscodeBackend],
        resource_gate: ResourceGate,
        catalog: OutputCatalog | None = None,
    ) -> None:
        paths = TrackArtifactPaths(work_dir, dest_dir)
        resolved_catalog = catalog or SqliteOutputCatalog(work_dir / "catalog.db")
        self.catalog = resolved_catalog
        self.scheduler = TranscodeScheduler(backends, resource_gate, resolved_catalog)
        self.transcode_service = JobTranscodeService(
            job_store,
            self.scheduler,
            PathTrackArtifactProbe(paths),
            TrackStateMachine(),
        )
