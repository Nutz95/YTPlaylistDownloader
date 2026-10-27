from typing import Protocol

from ytpd.domain.transcode_progress_snapshot import TranscodeProgressSnapshot


class TranscodeProgressStore(Protocol):
    """Thread-safe live transcode progress keyed by track id."""

    def set_snapshot(self, snapshot: TranscodeProgressSnapshot) -> None:
        """Replace the snapshot for ``snapshot.track_id``."""

    def get_snapshot(self, track_id: str) -> TranscodeProgressSnapshot | None:
        """Return the latest snapshot for ``track_id``, if any."""

    def clear(self, track_id: str) -> None:
        """Drop progress for ``track_id`` when the encode finishes."""
