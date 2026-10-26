from typing import Protocol

from ytpd.domain.download_result import DownloadResult
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef


class MediaDownloader(Protocol):
    """Download one track's YouTube media into the job work directory."""

    def download(self, job: JobSnapshot, track: TrackRef) -> DownloadResult:
        """Download ``track`` for ``job`` and return a typed result."""
