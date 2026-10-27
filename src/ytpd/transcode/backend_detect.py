from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.ports.transcode_backend import TranscodeBackend
from ytpd.transcode.cpu_parallelism import CpuParallelism
from ytpd.transcode.ffmpeg_kind_worker import FfmpegKindWorker
from ytpd.transcode.gpu_capability_probe import GpuCapabilityProbe


class BackendDetect:
    """Build the ordered backend pool from live hardware capability probes."""

    def __init__(
        self,
        paths: TrackArtifactPaths,
        cpu_parallelism: CpuParallelism,
        capability_probe: GpuCapabilityProbe | None = None,
    ) -> None:
        self._paths = paths
        self._cpu_parallelism = cpu_parallelism
        self._capability_probe = capability_probe or GpuCapabilityProbe()

    def detect(self) -> list[TranscodeBackend]:
        """Return backends in GPU-first priority order for available devices."""
        backends: list[TranscodeBackend] = []
        if self._capability_probe.has_nvidia():
            backends.append(
                FfmpegKindWorker(self._paths, TranscodeBackendKind.NVIDIA)
            )
        if self._capability_probe.has_arc():
            backends.append(FfmpegKindWorker(self._paths, TranscodeBackendKind.ARC))
        for _ in range(self._cpu_parallelism.worker_count()):
            backends.append(FfmpegKindWorker(self._paths, TranscodeBackendKind.CPU))
        return backends
