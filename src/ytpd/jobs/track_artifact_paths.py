from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef


class TrackArtifactPaths:
    """Canonical relative artefact paths under work_dir and dest_dir."""

    def __init__(self, work_dir: Path, dest_dir: Path) -> None:
        self._work_dir = work_dir
        self._dest_dir = dest_dir

    def download_complete_marker(self, job: JobSnapshot, track: TrackRef) -> Path:
        """Path of the sidecar that marks a finished download for ``track``."""
        return self._work_dir / job.job_id / f"{track.track_id}.download"

    def destination_mp3(self, track: TrackRef) -> Path:
        """Path of the destination MP3 for ``track``."""
        return self._dest_dir / f"{track.track_id}.mp3"
