from pathlib import Path

from ytpd.domain.download_attempt_mode import DownloadAttemptMode


class DownloadResumePolicy:
    """Choose resume vs full re-download from partial artefact presence."""

    def decide(self, partial_path: Path) -> DownloadAttemptMode:
        """Return RESUME when a non-empty partial file exists."""
        if partial_path.is_file() and partial_path.stat().st_size > 0:
            return DownloadAttemptMode.RESUME
        return DownloadAttemptMode.FULL

    def clear_partial(self, partial_path: Path) -> None:
        """Delete a failed partial so the next attempt is a full download."""
        if partial_path.is_file():
            partial_path.unlink()
