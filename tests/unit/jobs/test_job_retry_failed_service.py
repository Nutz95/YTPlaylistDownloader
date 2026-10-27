from dataclasses import replace
from pathlib import Path

from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_retry_failed_service import JobRetryFailedService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.path_track_artifact_probe import PathTrackArtifactProbe
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


def test_retry_failed_resets_match_failed_tracks(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    job = store.create("https://example.test/list")
    failed = TrackRef(
        track_id="t1",
        title="Song",
        artist="Artist",
        duration_sec=10,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.MATCH_FAILED,
        youtube_url=None,
        deezer_id="1",
        error_message="réponse chat LM Studio vide",
    )
    store.save(replace(job, status=JobStatus.CANCELLED, tracks=[failed]))
    updated = JobRetryFailedService(
        store,
        PathTrackArtifactProbe(paths),
        paths,
    ).retry_failed(job.job_id)
    assert updated.status is JobStatus.INTERRUPTED
    assert updated.tracks[0].phase is TrackPhase.RESOLVED
    assert updated.tracks[0].error_message is None
