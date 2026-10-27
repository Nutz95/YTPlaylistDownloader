from typing import Protocol

from ytpd.domain.download_progress_snapshot import DownloadProgressSnapshot


class DownloadProgressStore(Protocol):
    """Thread-safe live download progress keyed by shared media identity."""

    def set_snapshot(self, snapshot: DownloadProgressSnapshot) -> None:
        """Replace the snapshot for ``snapshot.media_key``."""

    def get_snapshot(self, media_key: str) -> DownloadProgressSnapshot | None:
        """Return the latest snapshot for ``media_key``, if any."""

    def clear(self, media_key: str) -> None:
        """Drop progress for ``media_key`` when the download finishes."""
