from pathlib import Path

from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore


def test_save_load_preserves_tracks(tmp_path: Path) -> None:
    store = SqliteJobCheckpointStore(tmp_path / "jobs.db")
    snapshot = JobSnapshot(
        job_id="job-1",
        source_url="https://youtu.be/abc",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.QUEUED,
        tracks=[
            TrackRef(
                track_id="t1",
                title="Song",
                artist="Artist",
                duration_sec=120,
                source_kind=SourceKind.YOUTUBE_VIDEO,
                phase=TrackPhase.RESOLVED,
                youtube_url="https://youtu.be/abc",
                deezer_id=None,
                error_message=None,
            )
        ],
        error_message=None,
    )
    store.save(snapshot)
    loaded = store.load("job-1")
    assert loaded is not None
    assert loaded.job_id == "job-1"
    assert len(loaded.tracks) == 1
    assert loaded.tracks[0].title == "Song"
    assert loaded.tracks[0].youtube_url == "https://youtu.be/abc"
