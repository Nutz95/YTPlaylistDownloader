from concurrent.futures import ThreadPoolExecutor
from functools import partial

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.ports.media_downloader import MediaDownloader


class DownloadPool:
    """Download many tracks in parallel using an injected media downloader."""

    def __init__(self, downloader: MediaDownloader, max_workers: int) -> None:
        self._downloader = downloader
        self._max_workers = max(1, max_workers)

    def run(self, job: JobSnapshot, tracks: list[TrackRef]) -> list[DownloadResult]:
        """Download each track and return results in input order."""
        if len(tracks) == 0:
            return []
        worker = partial(self._downloader.download, job)
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            return list(pool.map(worker, tracks))
