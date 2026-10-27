import threading
from dataclasses import replace
from pathlib import Path

from ytpd.catalog.memory_output_catalog import MemoryOutputCatalog
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.domain.transcode_backend_kind import TranscodeBackendKind
from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_download_transcode_coordinator import (
    JobDownloadTranscodeCoordinator,
)
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_phase_healer import TrackPhaseHealer
from ytpd.jobs.track_state_machine import TrackStateMachine
from ytpd.runtime.gpu_resource_gate import GpuResourceGate
from ytpd.transcode.transcode_scheduler import TranscodeScheduler
from tests.fakes.blocking_cancel_media_downloader import BlockingCancelMediaDownloader
from tests.fakes.fake_media_downloader import FakeMediaDownloader
from tests.fakes.fake_transcode_backend import FakeTranscodeBackend


def _matched_track(track_id: str, title: str) -> TrackRef:
    return TrackRef(
        track_id=track_id,
        title=title,
        artist="Artist",
        duration_sec=10,
        source_kind=SourceKind.YOUTUBE_PLAYLIST,
        phase=TrackPhase.MATCHED,
        youtube_url=f"https://youtu.be/{track_id}",
        deezer_id=None,
        error_message=None,
    )


def _coordinator(
    store: JobStore,
    paths: TrackArtifactPaths,
    downloader: FakeMediaDownloader,
    backend: FakeTranscodeBackend,
    cancel_flag: JobCancelFlag,
) -> JobDownloadTranscodeCoordinator:
    probe = PathTrackArtifactProbe(paths)
    return JobDownloadTranscodeCoordinator(
        store,
        DownloadPool(downloader, max_workers=2, cancel_flag=cancel_flag),
        TranscodeScheduler(
            [backend],
            GpuResourceGate(),
            MemoryOutputCatalog(),
        ),
        probe,
        TrackStateMachine(),
        paths,
        cancel_flag,
        JobFailureLog(paths),
        TrackPhaseHealer(probe),
    )


def test_transcode_starts_before_slow_download_finishes(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    cancel_flag = JobCancelFlag()
    downloader = FakeMediaDownloader(
        paths,
        {"fast", "slow"},
        delay_sec_by_id={"fast": 0.0, "slow": 0.35},
    )
    seen_overlap = threading.Event()

    def _on_start(track: TrackRef) -> None:
        if track.track_id == "fast" and "slow" in downloader.in_progress:
            seen_overlap.set()

    backend = FakeTranscodeBackend(
        TranscodeBackendKind.CPU,
        paths,
        on_start=_on_start,
    )
    coordinator = _coordinator(store, paths, downloader, backend, cancel_flag)
    job = store.create("https://example.test/list")
    store.save(
        replace(
            job,
            status=JobStatus.RUNNING,
            tracks=[
                _matched_track("fast", "Fast"),
                _matched_track("slow", "Slow"),
            ],
        )
    )
    result = coordinator.run(job.job_id)
    assert all(track.phase is TrackPhase.DONE for track in result.tracks)
    assert seen_overlap.is_set()
    assert set(backend.calls) == {"fast", "slow"}


def test_cancel_stops_new_transcodes_after_flag(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    cancel_flag = JobCancelFlag()
    started = threading.Event()
    downloader = BlockingCancelMediaDownloader(paths, cancel_flag, started)
    backend = FakeTranscodeBackend(TranscodeBackendKind.CPU, paths)
    coordinator = _coordinator(store, paths, downloader, backend, cancel_flag)
    job = store.create("https://example.test/list")
    store.save(
        replace(
            job,
            status=JobStatus.RUNNING,
            tracks=[_matched_track("t1", "One"), _matched_track("t2", "Two")],
        )
    )

    def _run() -> None:
        coordinator.run(job.job_id)

    thread = threading.Thread(target=_run)
    thread.start()
    assert started.wait(timeout=2.0)
    cancel_flag.cancel()
    thread.join(timeout=5.0)
    assert thread.is_alive() is False
    assert backend.calls == []


def test_stuck_transcoding_without_mp3_is_retried(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    cancel_flag = JobCancelFlag()
    downloader = FakeMediaDownloader(paths, set())
    backend = FakeTranscodeBackend(TranscodeBackendKind.CPU, paths)
    coordinator = _coordinator(store, paths, downloader, backend, cancel_flag)
    job = store.create("https://example.test/list")
    track = replace(
        _matched_track("stuck", "Stuck"),
        phase=TrackPhase.TRANSCODING,
    )
    saved = store.save(
        replace(job, status=JobStatus.RUNNING, tracks=[track])
    )
    media = paths.download_media_file(saved, track)
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"audio")
    paths.download_complete_marker(saved, track).write_text("ok", encoding="utf-8")
    result = coordinator.run(saved.job_id)
    assert result.tracks[0].phase is TrackPhase.DONE
    assert backend.calls == ["stuck"]
    assert downloader.calls == []
