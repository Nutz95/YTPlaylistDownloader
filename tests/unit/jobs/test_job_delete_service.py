from dataclasses import replace
from pathlib import Path

import pytest

from tests.fakes.fake_active_job_id_reader import FakeActiveJobIdReader
from ytpd.domain.job_status import JobStatus
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_delete_service import JobDeleteService
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.jobs.track_artifact_paths import TrackArtifactPaths


def _store(tmp_path: Path) -> JobStore:
    return JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))


def test_delete_removes_checkpoint_and_work_dir(tmp_path: Path) -> None:
    store = _store(tmp_path)
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    service = JobDeleteService(store, FakeActiveJobIdReader(), paths)
    job = store.create("https://youtu.be/abc")
    completed = store.save(replace(job, status=JobStatus.COMPLETED))
    work = paths.job_work_dir(completed)
    work.mkdir(parents=True)
    (work / "failures.log").write_text("x", encoding="utf-8")

    service.delete(completed.job_id)

    assert store.get(completed.job_id) is None
    assert not work.exists()


def test_delete_unknown_job_raises(tmp_path: Path) -> None:
    store = _store(tmp_path)
    service = JobDeleteService(
        store,
        FakeActiveJobIdReader(),
        TrackArtifactPaths(tmp_path / "work", tmp_path / "out"),
    )
    with pytest.raises(InvalidJobError, match="job not found"):
        service.delete("missing")


def test_delete_running_job_raises(tmp_path: Path) -> None:
    store = _store(tmp_path)
    service = JobDeleteService(
        store,
        FakeActiveJobIdReader(),
        TrackArtifactPaths(tmp_path / "work", tmp_path / "out"),
    )
    job = store.create("https://youtu.be/abc")
    store.save(replace(job, status=JobStatus.RUNNING))
    with pytest.raises(InvalidJobError, match="cannot delete a running job"):
        service.delete(job.job_id)
    assert store.get(job.job_id) is not None


def test_delete_active_pipeline_job_raises(tmp_path: Path) -> None:
    store = _store(tmp_path)
    job = store.create("https://youtu.be/abc")
    store.save(replace(job, status=JobStatus.COMPLETED))
    service = JobDeleteService(
        store,
        FakeActiveJobIdReader(job.job_id),
        TrackArtifactPaths(tmp_path / "work", tmp_path / "out"),
    )
    with pytest.raises(InvalidJobError, match="cannot delete a running job"):
        service.delete(job.job_id)


def test_delete_completed_removes_only_completed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    service = JobDeleteService(store, FakeActiveJobIdReader(), paths)
    completed = store.create("https://youtu.be/done")
    store.save(replace(completed, status=JobStatus.COMPLETED))
    failed = store.create("https://youtu.be/fail")
    store.save(replace(failed, status=JobStatus.FAILED))
    queued = store.create("https://youtu.be/queue")
    work = paths.job_work_dir(completed)
    work.mkdir(parents=True)

    deleted = service.delete_completed()

    assert deleted == [completed.job_id]
    assert store.get(completed.job_id) is None
    assert store.get(failed.job_id) is not None
    assert store.get(queued.job_id) is not None
    assert not work.exists()


def test_delete_completed_skips_active_completed_job(tmp_path: Path) -> None:
    store = _store(tmp_path)
    paths = TrackArtifactPaths(tmp_path / "work", tmp_path / "out")
    blocked = store.create("https://youtu.be/blocked")
    store.save(replace(blocked, status=JobStatus.COMPLETED))
    other = store.create("https://youtu.be/other")
    store.save(replace(other, status=JobStatus.COMPLETED))
    service = JobDeleteService(
        store,
        FakeActiveJobIdReader(blocked.job_id),
        paths,
    )

    deleted = service.delete_completed()

    assert deleted == [other.job_id]
    assert store.get(blocked.job_id) is not None
    assert store.get(other.job_id) is None

