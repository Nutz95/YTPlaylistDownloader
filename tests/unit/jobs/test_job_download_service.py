from dataclasses import replace
from pathlib import Path

from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.job_download_service import JobDownloadService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.jobs.track_state_machine import TrackStateMachine
from tests.fakes.fake_media_downloader import FakeMediaDownloader


def test_download_job_persists_success_and_failure(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://www.youtube.com/playlist?list=x")
    tracks = [
        TrackRef(
            track_id="ok",
            title="Ok",
            artist="A",
            duration_sec=1,
            source_kind=SourceKind.YOUTUBE_PLAYLIST,
            phase=TrackPhase.MATCHED,
            youtube_url="https://youtu.be/ok",
            deezer_id=None,
            error_message=None,
        ),
        TrackRef(
            track_id="bad",
            title="Bad",
            artist="B",
            duration_sec=2,
            source_kind=SourceKind.YOUTUBE_PLAYLIST,
            phase=TrackPhase.MATCHED,
            youtube_url="https://youtu.be/bad",
            deezer_id=None,
            error_message=None,
        ),
    ]
    job = store.save(replace(job, tracks=tracks))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    service = JobDownloadService(
        store,
        DownloadPool(FakeMediaDownloader(paths, {"ok"}), max_workers=2),
        PathTrackArtifactProbe(paths),
        TrackStateMachine(),
        paths,
    )
    updated = service.download_job(job.job_id)
    by_id = {track.track_id: track for track in updated.tracks}
    assert by_id["ok"].phase is TrackPhase.DOWNLOADED
    assert by_id["bad"].phase is TrackPhase.ERROR
    assert paths.download_complete_marker(updated, by_id["ok"]).is_file()
