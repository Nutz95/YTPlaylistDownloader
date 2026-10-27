from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.fakes.build_test_app import BuildTestApp
from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
from ytpd.domain.job_status import JobStatus
from ytpd.domain.source_kind import SourceKind
from ytpd.domain.track_phase import TrackPhase
from ytpd.domain.track_ref import TrackRef
from ytpd.jobs.job_store import JobStore
from ytpd.jobs.sqlite_job_checkpoint_store import SqliteJobCheckpointStore
from ytpd.resolve.ytdlp_flat_playlist_parser import YtdlpFlatPlaylistParser

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_create_and_get_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abc"})
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "queued"
    assert body["tracks"] == []
    fetched = client.get(f"/api/jobs/{body['job_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["source_url"] == "https://youtu.be/abc"
    listed = client.get("/api/jobs")
    assert listed.status_code == 200
    jobs = listed.json()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["track_count"] == 0
    assert "tracks" not in jobs[0]


def test_progress_endpoint_for_empty_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abc"}).json()
    progress = client.get(f"/api/jobs/{created['job_id']}/progress")
    assert progress.status_code == 200
    body = progress.json()
    assert body["percent"] == 0.0
    assert body["active_media"] == []


def test_resume_job_starts_pipeline_with_resolve_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abc"}).json()
    resumed = client.post(f"/api/jobs/{created['job_id']}/resume")
    assert resumed.status_code == 200
    body = resumed.json()
    assert body["job_action"] == "resolve_playlist"
    assert body["decisions"] == []
    assert body["started"] is True


def test_resume_unknown_job_returns_404(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    response = client.post("/api/jobs/missing/resume")
    assert response.status_code == 404


def test_resolve_youtube_job_persists_tracks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    fixture = (_FIXTURES / "youtube_playlist_flat.json").read_text(encoding="utf-8")
    url = "https://www.youtube.com/playlist?list=PLtest"
    entries = YtdlpFlatPlaylistParser().parse(fixture)
    client = TestClient(
        BuildTestApp().build(
            tmp_path,
            ytdlp_client=FakeYtdlpFlatPlaylistClient({url: entries}),
        )
    )
    created = client.post("/api/jobs", json={"url": url}).json()
    resolved = client.post(f"/api/jobs/{created['job_id']}/resolve")
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["source_kind"] == "youtube_playlist"
    assert len(body["tracks"]) == 2
    again = client.post(f"/api/jobs/{created['job_id']}/resolve")
    assert again.status_code == 200
    assert again.json()["tracks"] == body["tracks"]


def test_youtube_override_marks_track_matched_and_starts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    failed = TrackRef(
        track_id="t1",
        title="Lose Yourself to Dance",
        artist="Daft Punk",
        duration_sec=300,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.ERROR,
        youtube_url="https://www.youtube.com/watch?v=Q3Bp1QVVieM",
        deezer_id="1",
        error_message="video not available",
    )
    store.save(replace(job, status=JobStatus.CANCELLED, tracks=[failed]))
    client = TestClient(BuildTestApp().build(tmp_path))
    response = client.post(
        f"/api/jobs/{job.job_id}/tracks/t1/youtube-override",
        json={"youtube_url": "https://youtu.be/NF-kLy44Hls"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["overridden"] is True
    assert body["started"] is True
    track = next(item for item in body["tracks"] if item["track_id"] == "t1")
    assert track["phase"] in {"matched", "downloading", "downloaded", "done", "error"}
    assert "NF-kLy44Hls" in track["youtube_url"]


def test_youtube_override_rejects_invalid_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
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
        error_message="no match",
    )
    store.save(replace(job, status=JobStatus.CANCELLED, tracks=[failed]))
    client = TestClient(BuildTestApp().build(tmp_path))
    response = client.post(
        f"/api/jobs/{job.job_id}/tracks/t1/youtube-override",
        json={"youtube_url": "https://example.test/x"},
    )
    assert response.status_code == 400


def test_youtube_override_rejects_running_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://example.test/list")
    failed = TrackRef(
        track_id="t1",
        title="Song",
        artist="Artist",
        duration_sec=10,
        source_kind=SourceKind.DEEZER_PLAYLIST,
        phase=TrackPhase.ERROR,
        youtube_url="https://www.youtube.com/watch?v=abc",
        deezer_id="1",
        error_message="fail",
    )
    store.save(replace(job, status=JobStatus.RUNNING, tracks=[failed]))
    client = TestClient(BuildTestApp().build(tmp_path))
    response = client.post(
        f"/api/jobs/{job.job_id}/tracks/t1/youtube-override",
        json={"youtube_url": "https://youtu.be/NF-kLy44Hls"},
    )
    assert response.status_code == 400


def test_delete_job_removes_from_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    created = client.post("/api/jobs", json={"url": "https://youtu.be/abc"}).json()
    job_id = created["job_id"]
    deleted = client.delete(f"/api/jobs/{job_id}")
    assert deleted.status_code == 200
    assert deleted.json()["ok"] is True
    listed = client.get("/api/jobs")
    assert listed.json()["jobs"] == []
    missing = client.get(f"/api/jobs/{job_id}")
    assert missing.status_code == 404


def test_delete_running_job_returns_409(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    store = JobStore(SqliteJobCheckpointStore(tmp_path / "jobs.db"))
    job = store.create("https://youtu.be/abc")
    store.save(replace(job, status=JobStatus.RUNNING))
    client = TestClient(BuildTestApp().build(tmp_path))
    response = client.delete(f"/api/jobs/{job.job_id}")
    assert response.status_code == 409
    assert "running" in response.json()["error"]
