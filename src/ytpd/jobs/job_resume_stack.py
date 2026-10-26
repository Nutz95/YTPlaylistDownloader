from pathlib import Path

from ytpd.jobs.job_resume_planner import JobResumePlanner
from ytpd.jobs.job_resume_service import JobResumeService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.job_checkpoint_store import JobCheckpointStore


class JobResumeStack:
    """Wire JobStore + resume planner/service for composition roots and tests."""

    def __init__(
        self,
        checkpoint_store: JobCheckpointStore,
        work_dir: Path,
        dest_dir: Path,
    ) -> None:
        self.job_store = JobStore(checkpoint_store)
        paths = TrackArtifactPaths(work_dir, dest_dir)
        planner = JobResumePlanner(
            TrackStateMachine(),
            PathTrackArtifactProbe(paths),
        )
        self.resume_service = JobResumeService(self.job_store, planner)
        self.planner = planner
