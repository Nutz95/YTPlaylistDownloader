from pathlib import Path

from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.transcode.backend_detect import BackendDetect
from ytpd.transcode.cpu_parallelism import CpuParallelism
from tests.fakes.fake_cpu_parallelism import FakeCpuParallelism


def test_backend_detect_is_cpu_only_pool(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    backends = BackendDetect(
        paths,
        FakeCpuParallelism(3),
        ffmpeg_path="ffmpeg-test",
    ).detect()
    assert len(backends) == 3
    assert all(backend.kind() is TranscodeBackendKind.CPU for backend in backends)


def test_backend_detect_matches_cpu_parallelism(tmp_path: Path) -> None:
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    count = CpuParallelism().worker_count()
    backends = BackendDetect(paths, CpuParallelism(), "ffmpeg").detect()
    assert len(backends) == count
