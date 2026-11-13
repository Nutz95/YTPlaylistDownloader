import shutil
from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class VideoOutputDeliverer:
    """Copy the downloaded full video file as-is into the destination folder."""

    def __init__(self, paths: TrackArtifactPaths) -> None:
        self._paths = paths

    def deliver(
        self,
        job: JobSnapshot,
        track: TrackRef,
        backend: TranscodeBackendKind,
    ) -> TranscodeResult:
        """Byte-copy the work video to the destination MP4 path."""
        source = self._paths.download_media_file(job, track)
        destination = self._paths.destination_file(job, track)
        if not source.is_file() or source.stat().st_size <= 0:
            return self._failure(track.track_id, backend, "missing download media")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._temporary_path(destination, track.track_id)
        self._unlink_quiet(temporary)
        try:
            shutil.copy2(source, temporary)
        except OSError as error:
            self._unlink_quiet(temporary)
            return self._failure(track.track_id, backend, f"video copy failed: {error}")
        if not temporary.is_file() or temporary.stat().st_size <= 0:
            self._unlink_quiet(temporary)
            return self._failure(
                track.track_id, backend, "video copy produced empty file"
            )
        temporary.replace(destination)
        return TranscodeResult(
            track_id=track.track_id,
            success=True,
            output_path=str(destination),
            backend=backend,
            error_message=None,
        )

    def _temporary_path(self, destination: Path, track_id: str) -> Path:
        safe_id = "".join(
            char if char.isalnum() or char in "-_" else "_" for char in track_id
        )
        return destination.parent / f".{safe_id}.mp4.tmp"

    def _unlink_quiet(self, path: Path) -> None:
        if not path.is_file():
            return
        try:
            path.unlink()
        except OSError:
            return

    def _failure(
        self,
        track_id: str,
        backend: TranscodeBackendKind,
        message: str,
    ) -> TranscodeResult:
        return TranscodeResult(
            track_id=track_id,
            success=False,
            output_path=None,
            backend=backend,
            error_message=message,
        )
