from pathlib import Path

import pytest

from ytpd.domain.job_media_mode import JobMediaMode
from ytpd.jobs.duplicate_source_url_error import DuplicateSourceUrlError
from ytpd.jobs.invalid_job_error import InvalidJobError
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore


def _store(tmp_path: Path) -> JobStore:
    return JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))


def test_create_rejects_empty_url(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(InvalidJobError, match="non-empty"):
        store.create("   ")


def test_create_rejects_duplicate_source_url(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first = store.create("https://youtu.be/abc")
    with pytest.raises(DuplicateSourceUrlError, match="already exists"):
        store.create("  https://youtu.be/abc  ")
    assert store.get(first.job_id) is not None
    assert len(store.list_jobs()) == 1


def test_create_allows_same_url_with_different_media_mode(tmp_path: Path) -> None:
    store = _store(tmp_path)
    audio = store.create("https://youtu.be/vid", JobMediaMode.AUDIO)
    video = store.create("https://youtu.be/vid", JobMediaMode.VIDEO)
    assert audio.job_id != video.job_id
    assert len(store.list_jobs()) == 2


def test_create_persists_video_media_mode(tmp_path: Path) -> None:
    store = _store(tmp_path)
    job = store.create("https://youtu.be/vid", JobMediaMode.VIDEO)
    loaded = store.get(job.job_id)
    assert loaded is not None
    assert loaded.media_mode is JobMediaMode.VIDEO
