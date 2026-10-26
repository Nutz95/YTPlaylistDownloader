from dataclasses import replace
from pathlib import Path

from ytpd.catalog.memory_output_catalog import MemoryOutputCatalog
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.runtime.gpu_resource_gate import GpuResourceGate
from ytpd.transcode.transcode_scheduler import TranscodeScheduler
from tests.fakes.fake_resource_gate import FakeResourceGate
from tests.fakes.fake_transcode_backend import FakeTranscodeBackend


def _track(track_id: str) -> TrackRef:
    return TrackRef(
        track_id=track_id,
        title=track_id,
        artist="A",
        duration_sec=1,
        source_kind=SourceKind.YOUTUBE_PLAYLIST,
        phase=TrackPhase.DOWNLOADED,
        youtube_url=f"https://youtu.be/{track_id}",
        deezer_id=None,
        error_message=None,
    )


def test_scheduler_prefers_nvidia_when_gpu_free(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://www.youtube.com/watch?v=a")
    job = store.save(replace(job, tracks=(_track("a"),)))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    media = paths.download_media_file(job, job.tracks[0])
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"audio")
    paths.download_complete_marker(job, job.tracks[0]).write_text("ok", encoding="utf-8")
    nvidia = FakeTranscodeBackend(TranscodeBackendKind.NVIDIA, paths)
    cpu = FakeTranscodeBackend(TranscodeBackendKind.CPU, paths)
    catalog = MemoryOutputCatalog()
    results = TranscodeScheduler(
        [nvidia, cpu],
        FakeResourceGate(),
        catalog,
    ).run(job, list(job.tracks))
    assert results[0].success is True
    assert results[0].backend is TranscodeBackendKind.NVIDIA
    assert nvidia.calls == ["a"]
    assert cpu.calls == []
    assert len(catalog.list_entries()) == 1


def test_scheduler_skips_gpu_while_llm_held(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://www.youtube.com/watch?v=a")
    job = store.save(replace(job, tracks=(_track("a"),)))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    media = paths.download_media_file(job, job.tracks[0])
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"audio")
    gate = GpuResourceGate()
    gate.acquire_llm()
    nvidia = FakeTranscodeBackend(TranscodeBackendKind.NVIDIA, paths)
    cpu = FakeTranscodeBackend(TranscodeBackendKind.CPU, paths)
    results = TranscodeScheduler(
        [nvidia, cpu],
        gate,
        MemoryOutputCatalog(),
    ).run(job, list(job.tracks))
    gate.release_llm()
    assert results[0].success is True
    assert results[0].backend is TranscodeBackendKind.CPU
    assert nvidia.calls == []
    assert cpu.calls == ["a"]
