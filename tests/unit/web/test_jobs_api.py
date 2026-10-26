from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.fakes.build_test_app import BuildTestApp
from tests.fakes.fake_ytdlp_flat_playlist_client import FakeYtdlpFlatPlaylistClient
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


def test_resume_job_returns_resolve_plan(
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
    fetched = client.get(f"/api/jobs/{created['job_id']}")
    assert fetched.json()["status"] == "running"


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
