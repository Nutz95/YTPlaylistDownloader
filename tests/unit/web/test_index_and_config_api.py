from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.fakes.build_test_app import BuildTestApp


def test_index_contains_all_tabs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    response = client.get("/")
    assert response.status_code == 200
    assert 'data-tab="job"' in response.text
    assert 'data-tab="progress"' in response.text
    assert 'data-tab="config"' in response.text
    assert 'data-tab="catalogue"' in response.text
    assert 'href="/static/css/tokens.css"' in response.text
    assert 'id="job-list"' in response.text
    assert 'id="progress-job-select"' in response.text


def test_config_api_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(BuildTestApp().build(tmp_path))
    get_response = client.get("/api/config")
    assert get_response.status_code == 200
    payload = get_response.json()
    payload["work_dir"] = "work2"
    payload["dest_dir"] = "out2"
    put_response = client.put("/api/config", json=payload)
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["work_dir"] == "work2"
    assert (tmp_path / "work2").is_dir()
