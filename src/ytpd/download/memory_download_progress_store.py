import threading

from ytpd.domain.download_progress_snapshot import DownloadProgressSnapshot


class MemoryDownloadProgressStore:
    """In-process download progress map for UI polling."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_key: dict[str, DownloadProgressSnapshot] = {}

    def set_snapshot(self, snapshot: DownloadProgressSnapshot) -> None:
        """Replace the snapshot for ``snapshot.media_key``."""
        with self._lock:
            self._by_key[snapshot.media_key] = snapshot

    def get_snapshot(self, media_key: str) -> DownloadProgressSnapshot | None:
        """Return the latest snapshot for ``media_key``, if any."""
        with self._lock:
            return self._by_key.get(media_key)

    def clear(self, media_key: str) -> None:
        """Drop progress for ``media_key`` when the download finishes."""
        with self._lock:
            self._by_key.pop(media_key, None)
