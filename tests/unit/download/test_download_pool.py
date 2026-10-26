from dataclasses import replace
from pathlib import Path

from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.download.download_pool import DownloadPool
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from tests.fakes.fake_media_downloader import FakeMediaDownloader


def test_download_pool_runs_pending_tracks(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://www.youtube.com/playlist?list=x")
    tracks = (
        TrackRef(
            track_id="a",
            title="A",
            artist="X",
            duration_sec=1,
            source_kind=SourceKind.YOUTUBE_PLAYLIST,
            phase=TrackPhase.MATCHED,
            youtube_url="https://youtu.be/a",
            deezer_id=None,
            error_message=None,
        ),
        TrackRef(
            track_id="b",
            title="B",
            artist="Y",
            duration_sec=2,
            source_kind=SourceKind.YOUTUBE_PLAYLIST,
            phase=TrackPhase.MATCHED,
            youtube_url="https://youtu.be/b",
            deezer_id=None,
            error_message=None,
        ),
    )
    job = store.save(replace(job, tracks=tracks))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    downloader = FakeMediaDownloader(paths, {"a", "b"})
    results = DownloadPool(downloader, max_workers=2).run(job, list(tracks))
    assert [item.track_id for item in results] == ["a", "b"]
    assert all(item.success for item in results)
    assert set(downloader.calls) == {"a", "b"}
