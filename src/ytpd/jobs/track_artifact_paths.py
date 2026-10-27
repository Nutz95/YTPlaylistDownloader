from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.mp3_filename_sanitizer import Mp3FilenameSanitizer


class TrackArtifactPaths:
    """Canonical relative artefact paths under work_dir and dest_dir."""

    def __init__(self, work_dir: Path, dest_dir: Path) -> None:
        self._work_dir = work_dir
        self._dest_dir = dest_dir
        self._filename_sanitizer = Mp3FilenameSanitizer()

    def job_work_dir(self, job: JobSnapshot) -> Path:
        """Work directory dedicated to ``job`` artefacts."""
        return self._work_dir / job.job_id

    def download_media_key(self, track: TrackRef) -> str:
        """Stable key for shared download progress and artefact stems."""
        return self._download_stem(track)

    def download_media_file(self, job: JobSnapshot, track: TrackRef) -> Path:
        """Path of the downloaded media file for ``track`` (shared by chapters)."""
        return self.job_work_dir(job) / f"{self._download_stem(track)}.media"

    def download_partial_file(self, job: JobSnapshot, track: TrackRef) -> Path:
        """Path of the yt-dlp partial download for ``track``."""
        return self.job_work_dir(job) / f"{self._download_stem(track)}.media.part"

    def download_complete_marker(self, job: JobSnapshot, track: TrackRef) -> Path:
        """Path of the sidecar that marks a finished download for ``track``."""
        return self.job_work_dir(job) / f"{self._download_stem(track)}.download"

    def destination_mp3(self, track: TrackRef) -> Path:
        """Path of the destination MP3 for ``track`` (``Artist - Title`` naming)."""
        stem = self._filename_sanitizer.stem_for_track(
            track.artist,
            track.title,
            track.track_id,
        )
        if track.chapter_index is not None:
            return self._dest_dir / f"{track.chapter_index + 1:02d} - {stem}.mp3"
        return self._dest_dir / f"{stem}.mp3"

    def _download_stem(self, track: TrackRef) -> str:
        if track.parent_video_id is not None and track.parent_video_id.strip() != "":
            return track.parent_video_id.strip()
        return track.track_id
