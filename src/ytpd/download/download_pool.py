from collections.abc import Callable, Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from functools import partial

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.ports.media_downloader import MediaDownloader


class DownloadPool:
    """Download many tracks in parallel using an injected media downloader."""

    def __init__(
        self,
        downloader: MediaDownloader,
        max_workers: int,
        cancel_flag: JobCancelFlag,
    ) -> None:
        self._downloader = downloader
        self._max_workers = max(1, max_workers)
        self._cancel_flag = cancel_flag

    def run(self, job: JobSnapshot, tracks: list[TrackRef]) -> list[DownloadResult]:
        """Download each track and return results in input order."""
        if len(tracks) == 0:
            return []
        worker = partial(self._downloader.download, job)
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            return list(pool.map(worker, tracks))

    def iter_results(
        self,
        job: JobSnapshot,
        tracks: list[TrackRef],
    ) -> Iterator[DownloadResult]:
        """Yield download results as they finish; stop queueing when cancelled."""
        if len(tracks) == 0:
            return
        worker: Callable[[TrackRef], DownloadResult] = partial(
            self._downloader.download, job
        )
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            yield from self._drain(pool, worker, tracks)

    def _drain(
        self,
        pool: ThreadPoolExecutor,
        worker: Callable[[TrackRef], DownloadResult],
        tracks: list[TrackRef],
    ) -> Iterator[DownloadResult]:
        queue = list(tracks)
        in_flight: dict[Future[DownloadResult], TrackRef] = {}
        while queue or in_flight:
            while queue and len(in_flight) < self._max_workers:
                if self._cancel_flag.is_cancelled():
                    queue.clear()
                    break
                track = queue.pop(0)
                future = pool.submit(worker, track)
                in_flight[future] = track
            if len(in_flight) == 0:
                break
            done, _ = wait(list(in_flight.keys()), return_when=FIRST_COMPLETED)
            for future in done:
                in_flight.pop(future, None)
                yield future.result()
