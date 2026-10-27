from pathlib import Path

from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_phase_healer import TrackPhaseHealer
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.ports.media_downloader import MediaDownloader


class JobDownloadStack:
    """Wire media downloader + pool into a job download service."""

    def __init__(
        self,
        job_store: JobStore,
        work_dir: Path,
        dest_dir: Path,
        downloader: MediaDownloader,
        max_workers: int,
        cancel_flag: JobCancelFlag,
    ) -> None:
        paths = TrackArtifactPaths(work_dir, dest_dir)
        self.paths = paths
        self.cancel_flag = cancel_flag
        self.failure_log = JobFailureLog(paths)
        probe = PathTrackArtifactProbe(paths)
        self.phase_healer = TrackPhaseHealer(probe)
        self.download_pool = DownloadPool(
            downloader,
            max_workers=max_workers,
            cancel_flag=cancel_flag,
        )
        self.download_service = JobDownloadService(
            job_store,
            self.download_pool,
            probe,
            TrackStateMachine(),
            paths,
            cancel_flag,
            self.failure_log,
            self.phase_healer,
        )
