from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.transcode_backend import TranscodeBackend
from ytpd.transcode.cpu_parallelism import CpuParallelism
from ytpd.transcode.ffmpeg_kind_worker import FfmpegKindWorker


class BackendDetect:
    """Build the ordered backend pool: NVIDIA, Arc, then N CPU workers."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        cpu_parallelism: CpuParallelism,
        enable_nvidia: bool = True,
        enable_arc: bool = True,
    ) -> None:
        self._paths = paths
        self._cpu_parallelism = cpu_parallelism
        self._enable_nvidia = enable_nvidia
        self._enable_arc = enable_arc

    def detect(self) -> list[TranscodeBackend]:
        """Return backends in GPU-first priority order."""
        backends: list[TranscodeBackend] = []
        if self._enable_nvidia:
            backends.append(
                FfmpegKindWorker(self._paths, TranscodeBackendKind.NVIDIA)
            )
        if self._enable_arc:
            backends.append(FfmpegKindWorker(self._paths, TranscodeBackendKind.ARC))
        for _ in range(self._cpu_parallelism.worker_count()):
            backends.append(FfmpegKindWorker(self._paths, TranscodeBackendKind.CPU))
        return backends
