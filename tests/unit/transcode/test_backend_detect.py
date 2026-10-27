from pathlib import Path

from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.transcode.backend_detect import BackendDetect
from ytpd.transcode.cpu_parallelism import CpuParallelism
from tests.fakes.fake_gpu_capability_probe import FakeGpuCapabilityProbe


def test_backend_detect_skips_missing_gpus(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    backends = BackendDetect(
        paths,
        CpuParallelism(),
        FakeGpuCapabilityProbe(nvidia=False, arc=False),
    ).detect()
    assert all(backend.kind() is TranscodeBackendKind.CPU for backend in backends)
    assert len(backends) >= 1


def test_backend_detect_enables_nvidia_when_present(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    backends = BackendDetect(
        paths,
        CpuParallelism(),
        FakeGpuCapabilityProbe(nvidia=True, arc=False),
    ).detect()
    kinds = [backend.kind() for backend in backends]
    assert TranscodeBackendKind.NVIDIA in kinds
    assert TranscodeBackendKind.ARC not in kinds
