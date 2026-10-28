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
            ),
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


def test_list_jobs_preserves_insertion_order(tmp_path: Path) -> None:
    store = SqliteJobCheckpointStore(tmp_path / "jobs.db")
    first = JobSnapshot(
        job_id="zzzz-later-uuid",
        source_url="https://youtu.be/first",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.QUEUED,
        tracks=[],
        error_message=None,
    )
    second = JobSnapshot(
        job_id="aaaa-earlier-uuid",
        source_url="https://youtu.be/second",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.QUEUED,
        tracks=[],
        error_message=None,
    )
    store.save(first)
    store.save(second)
    listed = store.list_jobs()
    assert [job.job_id for job in listed] == [first.job_id, second.job_id]


def test_delete_removes_job(tmp_path: Path) -> None:
    store = SqliteJobCheckpointStore(tmp_path / "jobs.db")
    snapshot = JobSnapshot(
        job_id="job-del",
        source_url="https://youtu.be/del",
        source_kind=SourceKind.YOUTUBE_VIDEO,
        status=JobStatus.COMPLETED,
        tracks=[],
        error_message=None,
    )
    store.save(snapshot)
    assert store.delete("job-del") is True
    assert store.load("job-del") is None
    assert store.delete("job-del") is False
