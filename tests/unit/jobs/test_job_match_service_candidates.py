from dataclasses import replace
from pathlib import Path

from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_cancel_flag import JobCancelFlag
from ytpd.jobs.job_failure_log import JobFailureLog
from ytpd.jobs.job_match_service import JobMatchService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths
from ytpd.match.match_pool import MatchPool
from tests.fakes.rejecting_match_with_candidates import RejectingMatchWithCandidates


def test_match_failed_persists_candidates(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    cancel = JobCancelFlag()
    service = JobMatchService(
        store,
        MatchPool(RejectingMatchWithCandidates(), max_workers=1, cancel_flag=cancel),
        cancel,
        JobFailureLog(paths),
    )
    job = store.create("https://example.test/list")
    store.save(
        replace(
            job,
            status=JobStatus.RUNNING,
            tracks=[
                TrackRef(
                    track_id="t1",
                    title="Song",
                    artist="Artist",
                    duration_sec=120,
                    source_kind=SourceKind.DEEZER_PLAYLIST,
                    phase=TrackPhase.RESOLVED,
                    youtube_url=None,
                    deezer_id="1",
                    error_message=None,
                )
            ],
        )
    )
    result = service.match_job(job.job_id)
    assert result.tracks[0].phase is TrackPhase.MATCH_FAILED
    assert len(result.tracks[0].match_candidates) == 1
    assert result.tracks[0].match_candidates[0].youtube_url.endswith("abc123")
