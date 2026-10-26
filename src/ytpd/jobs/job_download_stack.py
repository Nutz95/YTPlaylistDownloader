from pathlib import Path

from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
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
    ) -> None:
        paths = TrackArtifactPaths(work_dir, dest_dir)
        self.download_service = JobDownloadService(
            job_store,
            DownloadPool(downloader, max_workers=max_workers),
            PathTrackArtifactProbe(paths),
            TrackStateMachine(),
            paths,
        )
