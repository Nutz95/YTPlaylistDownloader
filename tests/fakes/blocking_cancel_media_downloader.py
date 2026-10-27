import threading
import time

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from tests.fakes.fake_media_downloader import FakeMediaDownloader


class BlockingCancelMediaDownloader(FakeMediaDownloader):
    """Block in download until the shared cancel flag is set."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        cancel_flag: JobCancelFlag,
        started: threading.Event,
    ) -> None:
        super().__init__(paths, set())
        self._cancel_flag = cancel_flag
        self._started = started

    def download(self, job: JobSnapshot, track: TrackRef) -> DownloadResult:
        """Wait until cancelled, then return a failed download result."""
        self._started.set()
        while not self._cancel_flag.is_cancelled():
            time.sleep(0.02)
        return DownloadResult(
            track_id=track.track_id,
            success=False,
            output_path=None,
            error_message="cancelled",
            bytes_downloaded=0,
        )
