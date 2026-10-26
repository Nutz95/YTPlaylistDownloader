from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.transcode.ffmpeg_mp3_encoder import FfmpegMp3Encoder


class FfmpegKindWorker:
    """MP3 worker labelled by backend kind (shared ffmpeg encode path)."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        kind: TranscodeBackendKind,
    ) -> None:
        self._paths = paths
        self._kind = kind
        self._encoder = FfmpegMp3Encoder()

    def kind(self) -> TranscodeBackendKind:
        """Return the configured backend kind."""
        return self._kind

    def transcode(self, job: JobSnapshot, track: TrackRef) -> TranscodeResult:
        """Encode downloaded media for ``track`` to destination MP3."""
        return self._encoder.encode(
            track.track_id,
            self._paths.download_media_file(job, track),
            self._paths.destination_mp3(track),
            self._kind,
        )
