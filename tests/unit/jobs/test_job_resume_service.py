from pathlib import Path

import pytest

from tests.fakes.fake_track_artifact_probe import FakeTrackArtifactProbe
from ytpd.domain.job_snapshot import JobSnapshot
from ytpd.domain.job_status import JobStatus
from ytpd.domain.resume_action import ResumeAction
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_artifact_flags import TrackArtifactFlags
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_resume_planner import JobResumePlanner
from ytpd.jobs.job_resume_service import JobResumeService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_state_machine import TrackStateMachine


def _planner(
    flags: dict[str, TrackArtifactFlags],
) -> JobResumePlanner:
    return JobResumePlanner(TrackStateMachine(), FakeTrackArtifactProbe(flags))


def test_empty_tracks_plan_resolves_playlist(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    plan = _planner({}).plan(job)
    assert plan.job_action is ResumeAction.RESOLVE_PLAYLIST
    assert plan.decisions == []
    assert plan.is_actionable() is True


def test_tracks_present_skip_resolve_and_choose_actions(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    created = store.create("https://example.test/list")
    tracks = [
        TrackRef(
            track_id="a",
            title="A",
            artist="X",
            duration_sec=1,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.RESOLVED,
            youtube_url=None,
            deezer_id="1",
            error_message=None,
        ),
        TrackRef(
            track_id="b",
            title="B",
            artist="Y",
            duration_sec=2,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            phase=TrackPhase.MATCHED,
            youtube_url="https://youtu.be/b",
            deezer_id="2",
            error_message=None,
        ),
    ]
    job = store.save(
        JobSnapshot(
            job_id=created.job_id,
            source_url=created.source_url,
            source_kind=SourceKind.DEEZER_PLAYLIST,
            status=JobStatus.INTERRUPTED,
            tracks=tracks,
            error_message=None,
        )
    )
    plan = _planner(
        {
            "a": TrackArtifactFlags(False, False),
            "b": TrackArtifactFlags(False, False),
        }
    ).plan(job)
    assert plan.job_action is ResumeAction.NONE
    assert plan.decisions[0].action is ResumeAction.MATCH
    assert plan.decisions[1].action is ResumeAction.DOWNLOAD


def test_stale_running_marked_interrupted(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    created = store.create("https://example.test/list")
    store.save(created.with_status(JobStatus.RUNNING))
    service = JobResumeService(store, _planner({}))
    updated = service.mark_stale_running_interrupted()
    assert len(updated) == 1
    assert updated[0].status is JobStatus.INTERRUPTED


def test_resume_job_rejects_completed(tmp_path: Path) -> None:
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    created = store.create("https://example.test/list")
    store.save(created.with_status(JobStatus.COMPLETED))
    service = JobResumeService(store, _planner({}))
    with pytest.raises(InvalidJobError, match="not resumable"):
        service.resume_job(created.job_id)
