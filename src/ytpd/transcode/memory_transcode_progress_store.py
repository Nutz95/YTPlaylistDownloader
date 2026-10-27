import threading

from ytpd.domain.transcode_progress_snapshot import TranscodeProgressSnapshot


class MemoryTranscodeProgressStore:
    """In-memory map of track id to the latest encode progress snapshot."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_track: dict[str, TranscodeProgressSnapshot] = {}

    def set_snapshot(self, snapshot: TranscodeProgressSnapshot) -> None:
        """Replace the snapshot for ``snapshot.track_id``."""
        with self._lock:
            self._by_track[snapshot.track_id] = snapshot

    def get_snapshot(self, track_id: str) -> TranscodeProgressSnapshot | None:
        """Return the latest snapshot for ``track_id``, if any."""
        with self._lock:
            return self._by_track.get(track_id)

    def clear(self, track_id: str) -> None:
        """Drop progress for ``track_id`` when the encode finishes."""
        with self._lock:
            self._by_track.pop(track_id, None)
