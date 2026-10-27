from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.transcode_backend import TranscodeBackend
from ytpd.ports.transcode_progress_store import TranscodeProgressStore
from ytpd.runtime.subprocess_text_runner import SubprocessTextRunner
from ytpd.transcode.cpu_parallelism import CpuParallelism
from ytpd.transcode.ffmpeg_kind_worker import FfmpegKindWorker


class BackendDetect:
    """Build the CPU MP3 worker pool (libmp3lame; no fake GPU backends)."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        cpu_parallelism: CpuParallelism,
        ffmpeg_path: str,
        progress_store: TranscodeProgressStore | None = None,
        runner: SubprocessTextRunner | None = None,
    ) -> None:
        cleaned = ffmpeg_path.strip()
        if cleaned == "":
            raise ValueError("ffmpeg_path must be a non-empty string")
        self._paths = paths
        self._cpu_parallelism = cpu_parallelism
        self._ffmpeg_path = cleaned
        self._progress_store = progress_store
        self._runner = runner or SubprocessTextRunner()

    def detect(self) -> list[TranscodeBackend]:
        """Return one CPU worker per parallelism slot."""
        return [
            FfmpegKindWorker(
                self._paths,
                TranscodeBackendKind.CPU,
                self._runner,
                self._ffmpeg_path,
                self._progress_store,
            )
            for _ in range(self._cpu_parallelism.worker_count())
        ]
