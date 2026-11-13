from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.domain.transcode_result import TranscodeResult
from ytpd.transcode.ffmpeg_kind_worker import FfmpegKindWorker
from ytpd.transcode.video_output_deliverer import VideoOutputDeliverer


class MediaOutputBackend:
    """Route audio encodes and full-video copies behind one transcode port."""

    def __init__(
        self,
        audio_worker: FfmpegKindWorker,
        video_deliverer: VideoOutputDeliverer,
    ) -> None:
        self._audio_worker = audio_worker
        self._video_deliverer = video_deliverer

    def kind(self) -> TranscodeBackendKind:
        """Return the audio worker kind used for pool/GPU scheduling."""
        return self._audio_worker.kind()

    def transcode(self, job: JobSnapshot, track: TrackRef) -> TranscodeResult:
        """Encode MP3 or copy the full video according to ``job.media_mode``."""
        if job.media_mode is JobMediaMode.VIDEO:
            return self._video_deliverer.deliver(job, track, self.kind())
        return self._audio_worker.transcode(job, track)
