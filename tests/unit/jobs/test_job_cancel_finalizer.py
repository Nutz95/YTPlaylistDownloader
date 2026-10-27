from dataclasses import replace
from pathlib import Path

from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_cancel_finalizer import JobCancelFinalizer
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore


def test_cancel_finalizer_marks_cancelled_and_freezes_matching(
    tmp_path: Path,
) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    track = TrackRef(
        track_id="t1",
        title="Song",
        artist="Artist",
        duration_sec=10,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.MATCHING,
        youtube_url=None,
        deezer_id="1",
        error_message=None,
    )
    store.save(replace(job, status=JobStatus.RUNNING, tracks=[track]))
    finalized = JobCancelFinalizer(store).finalize(job.job_id)
    assert finalized is not None
    assert finalized.status is JobStatus.CANCELLED
    assert finalized.tracks[0].phase is TrackPhase.RESOLVED
    assert finalized.error_message == "cancelled by user"
