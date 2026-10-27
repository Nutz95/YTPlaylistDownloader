from ytpd.domain.ffmpeg_encode_request import FfmpegEncodeRequest
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.transcode_progress_store import TranscodeProgressStore
from ytpd.runtime.subprocess_text_runner import SubprocessTextRunner
from ytpd.transcode.ffmpeg_mp3_encoder import FfmpegMp3Encoder


class FfmpegKindWorker:
    """MP3 worker labelled by backend kind (shared ffmpeg encode path)."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        kind: TranscodeBackendKind,
        runner: SubprocessTextRunner,
        ffmpeg_path: str,
        progress_store: TranscodeProgressStore | None = None,
    ) -> None:
        self._paths = paths
        self._kind = kind
        self._encoder = FfmpegMp3Encoder(
            runner,
            ffmpeg_path,
            progress_store=progress_store,
        )

    def kind(self) -> TranscodeBackendKind:
        """Return the configured backend kind."""
        return self._kind

    def transcode(self, job: JobSnapshot, track: TrackRef) -> TranscodeResult:
        """Encode downloaded media for ``track`` to destination MP3."""
        chapter_start = track.chapter_start_sec
        chapter_end = track.chapter_end_sec
        duration: float | None = None
        if chapter_start is not None and chapter_end is not None:
            duration = chapter_end - chapter_start
        elif track.duration_sec is not None and track.duration_sec > 0:
            duration = float(track.duration_sec)
        return self._encoder.encode(
            FfmpegEncodeRequest(
                track_id=track.track_id,
                source=self._paths.download_media_file(job, track),
                destination=self._paths.destination_mp3(track),
                backend=self._kind,
                chapter_start_sec=chapter_start,
                chapter_duration_sec=duration
                if chapter_start is not None and chapter_end is not None
                else None,
                metadata_title=track.title,
                metadata_artist=track.artist,
                expected_duration_sec=duration,
            )
        )
