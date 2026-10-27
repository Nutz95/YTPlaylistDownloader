from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.progress_calculator import ProgressCalculator


def test_global_percent_and_active_media_filter() -> None:
    job = JobSnapshot(
        job_id="j1",
        source_url="https://example.test/list",
        source_kind=SourceKind.YOUTUBE_PLAYLIST,
        status=JobStatus.RUNNING,
        tracks=[
            TrackRef(
                track_id="1",
                title="Done",
                artist="A",
                duration_sec=10,
                source_kind=SourceKind.YOUTUBE_PLAYLIST,
                phase=TrackPhase.DONE,
                youtube_url="https://youtu.be/1",
                deezer_id=None,
                error_message=None,
            ),
            TrackRef(
                track_id="2",
                title="DL",
                artist="B",
                duration_sec=20,
                source_kind=SourceKind.YOUTUBE_PLAYLIST,
                phase=TrackPhase.DOWNLOADING,
                youtube_url="https://youtu.be/2",
                deezer_id=None,
                error_message=None,
            ),
        ],
        error_message=None,
    )
    snapshot = ProgressCalculator().from_job(job)
    assert snapshot.global_progress.percent == 50.0
    assert len(snapshot.active_media) == 1
    assert snapshot.active_media[0].track_id == "2"
