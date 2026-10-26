import threading

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


class FakeTranscodeBackend:
    """Write a destination MP3 and record which tracks this backend handled."""

    def __init__(
        self,
        kind_value: TranscodeBackendKind,
        paths: TrackArtifactPaths,
        delay_sec: float = 0.0,
    ) -> None:
        self._kind = kind_value
        self._paths = paths
        self._delay_sec = delay_sec
        self.calls: list[str] = []
        self._lock = threading.Lock()

    def kind(self) -> TranscodeBackendKind:
        """Return the configured backend kind."""
        return self._kind

    def transcode(self, job: JobSnapshot, track: TrackRef) -> TranscodeResult:
        """Create a fake MP3 for ``track``."""
        if self._delay_sec > 0:
            threading.Event().wait(self._delay_sec)
        with self._lock:
            self.calls.append(track.track_id)
        destination = self._paths.destination_mp3(track)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"id3")
        return TranscodeResult(
            track_id=track.track_id,
            success=True,
            output_path=str(destination),
            backend=self._kind,
            error_message=None,
        )
